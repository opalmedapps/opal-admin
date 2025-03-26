"""This module provides forms for the `patients` app."""
import logging
from datetime import timedelta
from typing import Any, Optional, Union, cast

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db.models import QuerySet
from django.forms.fields import Field
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Div
from crispy_forms.layout import Field as CrispyField
from crispy_forms.layout import Hidden, Layout, Row, Submit
from dynamic_forms import DynamicField, DynamicFormMixin
from requests.exceptions import RequestException

from opal.caregivers.models import CaregiverProfile
from opal.core import validators
from opal.core.forms.layouts import CancelButton, EnterSuppressedLayout, FormActions, InlineSubmit, RadioSelect
from opal.core.forms.widgets import AvailableRadioSelect
from opal.hospital_settings.models import Institution
from opal.services.hospital.hospital import OIEService
from opal.services.hospital.hospital_data import OIEPatientData
from opal.services.twilio import TwilioService, TwilioServiceError
from opal.users.models import Caregiver, Language, User

from . import constants, utils
from .models import Patient, Relationship, RelationshipStatus, RelationshipType, RoleType, Site
from .validators import has_multiple_mrns_with_same_site_code, is_deceased

LOGGER = logging.getLogger(__name__)


# functions that are reused between two forms
def is_mrn_selected(form: forms.Form) -> bool:
    """
    Return whether MRN is selected as the card type.

    Args:
        form: the form object being used

    Returns:
        True, if MRN is selected, False otherwise
    """
    card_type: str = form['card_type'].value()
    return card_type == constants.MedicalCard.MRN.name


def is_not_mrn_or_single_site(form: forms.Form) -> bool:
    """
    Check whether the form's `card_type` doesn't have MRN selected or there is only one site.

    Args:
        form: the form object being used

    Returns:
        True if there is only one site or the selected `card_type` is MRN, False otherwise
    """
    site_count = Site.objects.all().count()

    return not is_mrn_selected(form) or site_count == 1


def get_site_empty_label(form: forms.Form) -> str:
    """
    Set the site empty label according to selected `card_type`.

    Args:
        form: the form object being used

    Returns:
        `Choose` if mrn is selected, `Not Required` otherwise
    """
    if is_mrn_selected(form):
        return cast(str, _('Choose...'))

    return cast(str, _('Not required'))


class DisableFieldsMixin(forms.Form):
    """Form mixin that has the ability to disable all form fields."""

    fields: dict[str, Field]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the mixin.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)  # noqa: WPS204 (overused expression)

        self.has_existing_data = False

    def disable_fields(self) -> None:
        """Disable all form fields."""
        for _field_name, field in self.fields.items():
            field.disabled = True

        self.has_existing_data = True


class AccessRequestManagementForm(forms.Form):
    """
    Management form for an access request.

    Tracks the current step during the process.
    """

    current_step = forms.CharField(widget=forms.HiddenInput())


class AccessRequestSearchPatientForm(DisableFieldsMixin, DynamicFormMixin, forms.Form):
    """Access request form that allows a user to search for a patient."""

    card_type = forms.ChoiceField(
        widget=forms.Select(attrs={'up-validate': ''}),
        choices=constants.MEDICAL_CARDS,
        initial=constants.MedicalCard.MRN.name,
        label=_('Card Type'),
    )
    site = DynamicField(
        forms.ModelChoiceField,
        queryset=Site.objects.all(),
        label=_('Hospital'),
        required=is_mrn_selected,
        disabled=is_not_mrn_or_single_site,
        empty_label=get_site_empty_label,
    )
    medical_number = forms.CharField(label=_('Identification Number'))

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        # store response for patient searched in hospital
        self.patient: Union[OIEPatientData, Patient, None] = None

        # initialize site with a site object when there is a single site and card type is mrn
        site_field: forms.ModelChoiceField = self.fields['site']  # type: ignore[assignment]
        sites: QuerySet[Site] = site_field.queryset  # type: ignore[assignment]

        if sites.count() == 1:
            site_field.widget = forms.HiddenInput()

            if is_mrn_selected(self):
                site_field.initial = sites.first()
        else:
            site_field.initial = None

        # TODO: potential improvement: make a mixin for all access request forms
        # that initializes the form helper and sets these two properties
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

        self.helper.layout = Layout(
            Div(
                'card_type',
                'medical_number',
                'site',
                # make form inline
                css_class='d-md-flex flex-row justify-content-start gap-3',
            ),
        )

    def clean_medical_number(self) -> str:
        """
        Validate the medical number depending on the type of card.

        Raises a `ValidationError` if the data is invalid.

        Returns:
            the cleaned medical number
        """
        # validate in specific field method even though it is reliant on card_type
        # is called after the required check
        card_type = self.cleaned_data.get('card_type')
        medical_number: str = self.cleaned_data['medical_number']

        if card_type == constants.MedicalCard.RAMQ.name:
            validators.validate_ramq(medical_number)

        # TODO: add MRN validation in the future if we know how to do it

        return medical_number

    def clean(self) -> dict[str, Any]:
        """
        Clean the form.

        If all data is valid performs the lookup/search for the patient.

        Returns:
            the cleaned data
        """
        super().clean()
        # initialize the OIEService to communicate with oie
        self.oie_service: OIEService = OIEService()

        card_type: Optional[str] = self.cleaned_data.get('card_type')
        medical_number: Optional[str] = self.cleaned_data.get('medical_number')
        site: Optional[Site] = self.cleaned_data.get('site')

        if card_type and medical_number:
            self._search_patient(card_type, medical_number, site)

        return self.cleaned_data

    def _search_patient(self, card_type: str, medical_number: str, site: Optional[Site]) -> None:
        """
        Perform patient search in `Patient` model then in OIE.

        Args:
            card_type: card type either ramq or mrn
            medical_number: medical number of the proper card type in string form
            site: `Site` object
        """
        response: dict[str, Any] = {}

        if card_type == constants.MedicalCard.RAMQ.name:
            self.patient = Patient.objects.filter(ramq=medical_number).first()
            if not self.patient:
                response = self.oie_service.find_patient_by_ramq(medical_number)
        # MRN
        elif card_type == constants.MedicalCard.MRN.name and site:
            self.patient = Patient.objects.filter(
                hospital_patients__mrn=medical_number,
                hospital_patients__site=site,
            ).first()

            if not self.patient:
                response = self.oie_service.find_patient_by_mrn(medical_number, site.acronym)

        if response:
            self._handle_response(response)

        if not self.patient and not self._errors:
            self.add_error(NON_FIELD_ERRORS, _('No patient could be found.'))

    def _handle_response(self, response: dict[str, Any]) -> None:
        """Handle the response from OIE service.

        Args:
            response: OIE service response
        """
        if response['status'] == 'success':
            self.patient = response['data']
        else:
            messages = response['data'].get('message')

            if 'connection_error' in messages:
                self.add_error(NON_FIELD_ERRORS, _('Could not establish a connection to the hospital interface.'))
            elif 'no_test_patient' in messages:
                self.add_error(NON_FIELD_ERRORS, _('Patient is not a test patient.'))


class AccessRequestConfirmPatientForm(DisableFieldsMixin, forms.Form):
    """
    Access request form that allows a user to confirm the found patient.

    This form does not contain any fields.
    This form can be validated after initialization to give early user feedback.
    Submitting the form (assuming it is valid) confirms that the correct patient was found.
    """

    # TODO: checkbox will be needed to be added at the end
    # move search buttons to inline with search
    # make form continue when clicking checkbox
    # "The correct patient was found and the patient data is correct"

    def __init__(self, patient: Patient | OIEPatientData, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the form with the patient search result.

        The patient can either be an existing patient or a search result from the hospital.

        Args:
            patient: a `Patient` or `OIEPatientData` instance
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        # pretend its bound so that it can be validated early
        self.is_bound = True
        # TODO: ensure that the form is validated early

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

        self.patient = patient

    def clean(self) -> dict[str, Any]:
        """
        Clean the form.

        Validates that the patient was found
        and that the found patient does not contain any errors
        preventing us to continue to proceed with the process.

        Returns:
            the cleaned data
        """
        super().clean()
        cleaned_data = self.cleaned_data

        if is_deceased(self.patient):
            self.add_error(
                NON_FIELD_ERRORS,
                _('Unable to complete action with this patient. Please contact Medical Records.'),
            )

        if isinstance(self.patient, OIEPatientData) and has_multiple_mrns_with_same_site_code(self.patient):
            self.add_error(
                NON_FIELD_ERRORS,
                _('Patient has more than one active MRN at the same hospital, please contact Medical Records.'),
            )

        return cleaned_data


class AccessRequestRequestorForm(DisableFieldsMixin, DynamicFormMixin, forms.Form):  # noqa: WPS214
    """This form provides a radio button to choose the relationship to the patient."""

    relationship_type = forms.ModelChoiceField(
        queryset=RelationshipType.objects.all().reverse(),
        widget=AvailableRadioSelect(attrs={'up-validate': ''}),
        label=_('Relationship to the patient'),
    )

    form_filled = DynamicField(
        forms.BooleanField,
        label=_('The requestor filled out the request form'),
        required=lambda form: form._form_required(),  # noqa: WPS437
    )

    id_checked = forms.BooleanField(label=_('Requestor ID checked'))

    user_type = forms.ChoiceField(
        choices=constants.USER_TYPES,
        initial=constants.UserType.NEW.name,
        widget=forms.RadioSelect(attrs={'up-validate': ''}),
    )

    first_name = DynamicField(
        forms.CharField,
        label=_('First Name'),
        required=lambda form: not form.is_existing_user_selected(),
        disabled=lambda form: form.is_patient_requestor(),
        initial=lambda form: form.patient.first_name if form.is_patient_requestor() else None,
    )
    last_name = DynamicField(
        forms.CharField,
        label=_('Last Name'),
        required=lambda form: not form.is_existing_user_selected(),
        disabled=lambda form: form.is_patient_requestor(),
        initial=lambda form: form.patient.last_name if form.is_patient_requestor() else None,
    )

    user_email = DynamicField(
        forms.EmailField,
        label=_('Email Address'),
        required=lambda form: form.is_existing_user_selected(),
    )
    user_phone = DynamicField(
        forms.CharField,
        label=_('Phone Number'),
        initial='+1',
        validators=[validators.validate_phone_number],
        required=lambda form: form.is_existing_user_selected(),
    )

    def __init__(  # noqa: WPS231 (too much cognitive complexity)
        self,
        patient: Patient | OIEPatientData,
        existing_user: Optional[CaregiverProfile] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the layout for card type select box and card number input box.

        Args:
            patient: a `Patient` or `OIEPatientData` instance
            existing_user: a `CaregiverProfile` if a user was previously found, None otherwise
            args: additional arguments
            kwargs: additional keyword arguments
        """
        # dynamic fields require the patient to be set
        self.patient = patient

        initial = kwargs.pop('initial', None)

        # remove empty first and last name if present in initial data
        # this allows us to provide the first and last name of the patient as initial data in the dynamic form field
        # this can happen when switching to "Self" and receiving an "up-validate" request
        # where we pass the existing data as initial to avoid form validation
        if initial:
            relationship_type = initial.get('relationship_type')
            # the relationship type is a string at this point
            is_patient_requestor = relationship_type == str(RelationshipType.objects.self_type().pk)

            if 'first_name' in initial and (not initial.get('first_name') or is_patient_requestor):
                initial.pop('first_name')
            if 'last_name' in initial and (not initial.get('last_name') or is_patient_requestor):
                initial.pop('last_name')

        kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

        self.existing_user: Optional[CaregiverProfile] = existing_user

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

        self.helper.layout = Layout(
            Row(
                Column(
                    RadioSelect('relationship_type'),
                ),
                Column(
                    # make it appear like a label
                    HTML('<p class="fw-semibold">{0}</p>'.format(_('Validation'))),
                    'form_filled',
                    'id_checked',
                ),
            ),
            TabRadioSelect('user_type'),
            # empty div to be filled below depending on the chosen user type
            Div(css_class='mb-4 p-3 border-start border-end border-bottom'),
        )

        if self.is_existing_user_selected():
            self.helper.layout[2].append(Layout(
                Row(
                    Column('user_email', css_class='col-4'),
                    Column('user_phone', css_class='col-4'),
                    Column(InlineSubmit('search_user', label=gettext('Find User'))),
                ),
                HTML('{% load render_table from django_tables2 %}{% render_table user_table %}'),
            ))
        # handle current value being None
        else:
            self.helper.layout[2].extend(Layout(
                Row(
                    Column('first_name', css_class='col-4'),
                    Column('last_name', css_class='col-4'),
                ),
            ))

        if isinstance(patient, Patient):
            relationship_types = utils.valid_relationship_types(patient)
        else:
            relationship_types = utils.search_relationship_types_by_patient_age(patient.date_of_birth)

        available_choices = relationship_types.values_list('id', flat=True)
        self.fields['relationship_type'].widget.available_choices = list(available_choices)
        self.fields['relationship_type'].widget.option_descriptions = self._build_tooltips()

    def is_patient_requestor(self) -> bool:
        """
        Return whether the patient is also the requestor.

        This is the case when a self relationship is selected.
        In the case of no selection, False is returned.

        Returns:
            True, if the selected relationship type is Self, False otherwise
        """
        relationship_type = self['relationship_type'].value()

        if relationship_type:
            return RelationshipType.objects.get(pk=relationship_type).role_type == RoleType.SELF

        return False

    def is_existing_user_selected(self, cleaned_data: Optional[dict[str, Any]] = None) -> bool:
        """
        Return whether the existing user option is selected.

        By default uses the bound field's value.
        Alternatively, the value can also be retrieved from the form's cleaned data.
        This is the preferred option if available.

        Args:
            cleaned_data: the form's cleaned data, None if not available

        Returns:
            True, if the existing user option is selected, False otherwise
        """
        user_type: Optional[str] = cleaned_data.get('user_type') if cleaned_data else self['user_type'].value()

        return user_type == constants.UserType.EXISTING.name

    def clean(self) -> dict[str, Any]:  # noqa: WPS231
        """
        Validate the form.

        Handle the "Existing user" selection by looking up the caregiver based on the inputs.

        Returns:
            the cleaned data
        """
        super().clean()
        cleaned_data = self.cleaned_data

        if self.is_existing_user_selected(cleaned_data):
            self._validate_existing_user_fields(cleaned_data)

            existing_user = self.existing_user
            patient = self.patient
            relationship_type = cleaned_data.get('relationship_type')

            if existing_user:
                if self.is_patient_requestor() and isinstance(patient, OIEPatientData):
                    self._validate_patient_requestor(patient, existing_user)

                if relationship_type:
                    patient_instance = patient if isinstance(patient, Patient) else None
                    self._validate_relationship(patient_instance, existing_user, relationship_type)

        return cleaned_data

    def _validate_existing_user_fields(self, cleaned_data: dict[str, Any]) -> None:
        """
        Validate the existing user selection by looking up the caregiver.

        Look up the caregiver by email **and** phone number.
        Add an error to the form if no user was found.

        Args:
            cleaned_data: the form's cleaned data, None if not available
        """
        cleaned_data = self.cleaned_data

        # at the beginning (empty form) they are not in the cleaned data
        if 'user_email' in cleaned_data and 'user_phone' in cleaned_data:
            user_email = cleaned_data['user_email']
            user_phone = cleaned_data['user_phone']

            self.existing_user = CaregiverProfile.objects.filter(
                user__email=user_email,
                user__phone_number=user_phone,
            ).first()

            # prevent continuing when no user was found
            if not self.existing_user:
                self.add_error(
                    NON_FIELD_ERRORS,
                    _('No existing user could be found.'),
                )

    def _validate_patient_requestor(self, patient: OIEPatientData, caregiver: CaregiverProfile) -> None:
        if patient.first_name != caregiver.user.first_name or patient.last_name != caregiver.user.last_name:
            self.add_error(
                NON_FIELD_ERRORS,
                _('A self-relationship was selected but the caregiver appears to be someone other than the patient.'),
            )

    def _validate_relationship(
        self, patient: Patient | None,
        caregiver: CaregiverProfile,
        relationship_type: RelationshipType,
    ) -> None:
        relationship = Relationship(
            patient=patient,
            caregiver=caregiver,
            type=relationship_type,
            status=RelationshipStatus.CONFIRMED,
        )
        # reuse the model's existing validation
        try:
            relationship.clean()
        except ValidationError as exc:
            for error in exc.error_dict.get(NON_FIELD_ERRORS, []):
                self.add_error(NON_FIELD_ERRORS, error)

    def _form_required(self) -> bool:
        # at form initialization the selected value is only the primary key
        relationship_type = RelationshipType.objects.filter(pk=self['relationship_type'].value()).first()

        if relationship_type:
            return relationship_type.form_required

        return True

    def _build_tooltips(self) -> dict[int, str]:
        """
        Build a dict with option id and tooltip content.

        Returns:
            a dict of tooltips with relationship type description and patient age
        """
        option_descriptions = {}
        age_tile = _('Age')
        older_age = _(' and older')
        for value in RelationshipType.objects.all().values():
            option_descriptions[value['id']] = '{description}, {age_title}: {start_age}{end_age}'.format(
                description=value['description'],
                age_title=age_tile,
                start_age=value['start_age'],
                end_age='-{age}'.format(age=value['end_age']) if value['end_age'] else older_age,
            )
        return option_descriptions


# TODO: move this to the core app
class AccessRequestConfirmForm(forms.Form):
    """This form provides a layout to confirm user password."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        strip=False,
        label=_('Please confirm access to patient data by entering your password.'),
    )

    def __init__(self, username: str, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for new user form.

        Args:
            username: the username of the current user
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

        self.helper.layout = Layout(
            Row(
                Column('password', css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
        )
        self.username = username

    def clean(self) -> dict[str, Any]:
        """
        Validate the user password.

        Returns:
            the cleaned form data
        """
        super().clean()
        password = self.cleaned_data.get('password')

        if password and not authenticate(username=self.username, password=password):
            self.add_error('password', _('The password you entered is incorrect. Please try again.'))

        return self.cleaned_data


# TODO: move to core form layouts?
# potential improvement: inherit from Container or LayoutObject to include the content
# and provide a method to add content at the right place
class TabRadioSelect(CrispyField):
    """
    Custom radio select widget to be used for visualizing choices as Bootstrap tabs.

    Triggers validation via `up-validate` on selection to let the form react to the selection.
    For example, the form can change the layout according to the selection.
    """

    template = 'patients/radioselect_tabs.html'


class AccessRequestSendSMSForm(forms.Form):
    """This form provides the ability to send SMS with a registration code."""

    language = forms.ChoiceField(
        label=_('Language'),
        choices=Language,
    )

    phone_number = forms.CharField(
        label=_('Phone Number'),
        initial='+1',
        validators=[validators.validate_phone_number],
    )

    def __init__(self, registration_code: str, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for the send SMS form.

        Args:
            registration_code: the registration code that can be sent to a phone number
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        self.registration_code = registration_code
        self.registration_code_valid_period = Institution.objects.get().registration_code_valid_period

        self.helper = FormHelper()
        self.helper.attrs = {'novalidate': '', 'up-submit': '', 'up-target': '#sendSMS'}
        self.helper.layout = Layout(
            Div(
                'language',
                CrispyField('phone_number', wrapper_class='col-5'),
                # wrap the submit button to not make it increase in size if the form has field errors
                Div(
                    InlineSubmit('send_sms', label=gettext('Send')),
                ),
                # make form inline
                css_class='d-md-flex flex-row justify-content-start gap-3',
            ),
        )

    def clean(self) -> Optional[dict[str, Any]]:  # noqa: WPS210 (too many local variables)
        """
        Send the SMS to the phone number if the form fields are valid.

        Returns:
            the cleaned form data
        """
        cleaned_data = self.cleaned_data
        language = cleaned_data.get('language')
        phone_number = cleaned_data.get('phone_number')

        registration_code = self.registration_code
        registration_code_valid_period = self.registration_code_valid_period

        if language and phone_number:
            url = f'{settings.OPAL_USER_REGISTRATION_URL}/#!/form/search?code={registration_code}'
            with override(language):
                message = gettext(
                    'Your Opal registration code is: {code}.'
                    + 'Please go to: {url}. Your code will be expire in {period} hours.',
                ).format(
                    code=registration_code,
                    url=url,
                    period=registration_code_valid_period,
                )

            twilio = TwilioService(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.SMS_FROM)

            try:
                twilio.send_sms(phone_number, message)
            except (TwilioServiceError, RequestException):
                self.add_error(NON_FIELD_ERRORS, gettext('An error occurred while sending the SMS'))
                LOGGER.exception(f'Sending SMS failed to {phone_number}')

        return cleaned_data


class RelationshipAccessForm(forms.ModelForm[Relationship]):
    """Form for updating `Relationship Caregiver Access`  record."""

    first_name = forms.CharField(
        label=_('First Name'),
    )
    last_name = forms.CharField(
        label=_('Last Name'),
    )
    type = forms.ModelChoiceField(  # noqa: A003
        widget=forms.Select(attrs={'up-validate': ''}),
        queryset=RelationshipType.objects.none(),
        label=_('Relationship'),
        empty_label=None,
    )
    status = forms.ChoiceField(
        label=_('Status'),
    )
    start_date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        label=_('Access Start'),
    )
    end_date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        label=_('Access End'),
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '4'}),
        label=_('Explanation for Change(s)'),
        required=False,
    )
    cancel_url = forms.CharField(
        widget=forms.widgets.HiddenInput(),
        required=False,
    )

    class Meta:
        model = Relationship
        fields = (
            'type',
            'start_date',
            'end_date',
            'status',
            'reason',
            'cancel_url',
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: WPS210
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super().__init__(*args, **kwargs)
        # get the RelationshipType record that corresponds to the instance
        existing_choice = RelationshipType.objects.filter(pk=self.instance.type.pk)
        available_choices: QuerySet[RelationshipType] = existing_choice

        caregiver_firstname_field: Field = self.fields['first_name']
        caregiver_lastname_field: Field = self.fields['last_name']

        # setting the value of caregiver first and last names
        caregiver_firstname_field.initial = self.instance.caregiver.user.first_name
        caregiver_lastname_field.initial = self.instance.caregiver.user.last_name

        # get the saved type
        initial_type: RelationshipType = self.instance.type
        # ensure that self cannot be changed
        if initial_type.role_type == RoleType.SELF:
            self.fields['type'].disabled = True
            # use readonly to include information in data post
            caregiver_firstname_field.widget.attrs['readonly'] = True
            caregiver_lastname_field.widget.attrs['readonly'] = True
            # change to required/not-required according to the type of the relationship
            self.fields['end_date'].required = False
        else:
            # get the selected type
            selected_type = self['type'].value()
            initial_type = RelationshipType.objects.get(pk=selected_type)
            # combine the instance value and with the valid relationshiptypes
            available_choices |= utils.valid_relationship_types(self.instance.patient)
            # exclude self relationship to disallow switching to self
            available_choices = available_choices.exclude(role_type=RelationshipType.objects.self_type())

        # set the type field with the proper choices
        self.fields['type'].queryset = available_choices  # type: ignore[attr-defined]

        self.fields['status'].choices = [  # type: ignore[attr-defined]
            (choice.value, choice.label) for choice in Relationship.valid_statuses(
                RelationshipStatus(self.instance.status),
            )
        ]
        self.fields['start_date'].widget.attrs.update({   # noqa: WPS219
            'min': self.instance.patient.date_of_birth,
            'max': Relationship.calculate_end_date(
                self.instance.patient.date_of_birth,
                initial_type,
            ),
        })
        self.fields['end_date'].widget.attrs.update({   # noqa: WPS219
            'min': self.instance.patient.date_of_birth + timedelta(days=1),
            'max': Relationship.calculate_end_date(
                self.instance.patient.date_of_birth,
                initial_type,
            ),
        })

        self.helper = FormHelper(self)
        self.helper.attrs = {'novalidate': ''}
        self.helper.layout = EnterSuppressedLayout(
            Row(
                CrispyField('first_name', wrapper_class='col-md-6'),
                CrispyField('last_name', wrapper_class='col-md-6'),
                CrispyField('type', wrapper_class='col-lg-3 col-md-6'),
                CrispyField('status', wrapper_class='col-lg-3 col-md-6 col-sm-12'),
                CrispyField('start_date', wrapper_class='col-lg-3 col-md-6 col-sm-12'),
                CrispyField('end_date', wrapper_class='col-lg-3 col-md-6 col-sm-12'),
                CrispyField('reason', wrapper_class='col-md-12'),
            ),
            Hidden('cancel_url', '{{cancel_url}}'),
            Row(
                FormActions(
                    Submit('submit', _('Save'), css_class='btn btn-primary me-2'),
                    CancelButton('{{cancel_url}}'),
                ),
            ),
        )

    def clean(self) -> dict[str, Any]:
        """
        Validate the that patient and caregiver have same names when relationship is of `SELF` type.

        Returns:
            the cleaned form data
        """
        super().clean()
        caregiver_firstname: Optional[str] = self.cleaned_data.get('first_name')
        caregiver_lastname: Optional[str] = self.cleaned_data.get('last_name')
        type_field: RelationshipType = cast(RelationshipType, self.cleaned_data.get('type'))

        if type_field.role_type == RoleType.SELF.name:
            if (
                self.instance.patient.first_name != caregiver_firstname
                or self.instance.patient.last_name != caregiver_lastname
            ):
                # this is to capture before saving patient and caregiver has matching names
                error = (_(
                    'A self-relationship was selected but the caregiver appears to be someone other than the patient.',
                ))
                self.add_error(NON_FIELD_ERRORS, error)

        return self.cleaned_data


# TODO Future Enhancement review UI and decide whether or not to add role_type as read-only field in UI.
class RelationshipTypeUpdateForm(forms.ModelForm[RelationshipType]):
    """Form for updating a `RelationshipType` object."""

    class Meta:
        model = RelationshipType
        fields = [
            'name_en',
            'name_fr',
            'description_en',
            'description_fr',
            'start_age',
            'end_age',
            'form_required',
            'can_answer_questionnaire',
        ]


class ManageCaregiverAccessForm(forms.Form):
    """Custom form for the manage caregiver access filter to customize cleaning the form."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the form.

        Handle dynamic form updates based on the current user selection.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        card_type: forms.ModelChoiceField = cast(forms.ModelChoiceField, self.fields['card_type'])
        site: forms.ModelChoiceField = cast(forms.ModelChoiceField, self.fields['site'])

        # add up-validate to `card_type` field to trigger post on change
        card_type.widget.attrs.update({'up-validate': ''})
        # check if mrn is selected to disable
        if is_mrn_selected(self):
            site.required = True
        else:
            site.disabled = True
            site.initial = None

        # get the proper empty value string for the selected `card_type`
        site.empty_label = get_site_empty_label(self)

        if Site.objects.all().count() == 1:
            site.disabled = True
            site.widget = forms.HiddenInput()
            site.initial = Site.objects.first()


class ManageCaregiverAccessUserForm(forms.ModelForm[User]):
    """Form for updating a `Caregiver` object."""

    class Meta:
        model = Caregiver
        fields = [
            'first_name',
            'last_name',
        ]
