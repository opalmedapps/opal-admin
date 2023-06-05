"""This module provides forms for the `patients` app."""
from datetime import date, timedelta
from typing import Any, Optional, Union

from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db.models import QuerySet
from django.forms.fields import Field
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, ButtonHolder, Column, Div
from crispy_forms.layout import Field as CrispyField
from crispy_forms.layout import Fieldset, Hidden, Layout, Row, Submit
from dynamic_forms import DynamicField, DynamicFormMixin

from opal.core import validators
from opal.core.forms.layouts import CancelButton, FormActions, InlineSubmit
from opal.core.forms.widgets import AvailableRadioSelect
from opal.services.hospital.hospital import OIEService
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData
from opal.users.models import Caregiver, User

from . import constants, utils
from .models import Patient, Relationship, RelationshipStatus, RelationshipType, RoleType, Site
from .validators import has_multiple_mrns_with_same_site_code, is_deceased


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
        super().__init__(*args, **kwargs)  # noqa: WPS204 (overused expression; move to setup.cfg?)

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


class AccessRequestSearchPatientForm(DisableFieldsMixin, DynamicFormMixin, forms.Form):  # noqa: WPS214
    """Access request form that allows a user to search for a patient."""

    card_type = forms.ChoiceField(
        widget=forms.Select(attrs={'up-validate': ''}),
        choices=constants.MEDICAL_CARDS,
        label=_('Card Type'),
    )
    site = DynamicField(
        forms.ModelChoiceField,
        queryset=Site.objects.all(),
        label=_('Hospital'),
        required=lambda form: form.is_mrn_selected(),
        disabled=lambda form: form.is_not_mrn_or_single_site(),
        empty_label=lambda form: _('Choose...') if form.is_mrn_selected() else _('Not required'),
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

            if self.is_mrn_selected():
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

        if not self.patient:
            self.add_error(NON_FIELD_ERRORS, _('No patient could be found.'))

        return self.cleaned_data

    def is_mrn_selected(self) -> bool:
        """
        Return whether MRN is selected as the card type.

        Returns:
            True, if MRN is selected, False otherwise
        """
        card_type: str = self['card_type'].value()
        return card_type == constants.MedicalCard.MRN.name

    def is_not_mrn_or_single_site(self) -> bool:
        """
        Check whether the form's `card_type` doesn't have MRN selected or there is only one site.

        Returns:
            True if there is only one site or the selected `card_type` is MRN, False otherwise
        """
        site_count = Site.objects.all().count()

        return not self.is_mrn_selected() or site_count == 1

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
                response = self.oie_service.find_patient_by_mrn(medical_number, site.code)

        self._handle_response(response)

    def _handle_response(self, response: dict[str, Any]) -> None:
        """Handle the response from OIE service.

        Args:
            response: OIE service response
        """
        if response:
            if response['status'] == 'success':
                self.patient = response['data']
            else:
                self.add_error(NON_FIELD_ERRORS, response['data']['message'])

    def _fake_oie_response(self) -> OIEPatientData:
        return OIEPatientData(
            date_of_birth=date.fromisoformat('2018-01-01'),
            first_name='Lisa',
            last_name='Simpson',
            sex='F',
            alias='',
            ramq='SIML86531906',
            ramq_expiration=None,
            deceased=False,
            death_date_time=None,
            mrns=[
                OIEMRNData(site='MGH', mrn='9999993', active=True),
                OIEMRNData(site='RVH', mrn='9999993', active=True),
            ],
        )


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


class AccessRequestRequestorForm(DisableFieldsMixin, DynamicFormMixin, forms.Form):
    """This form provides a radio button to choose the relationship to the patient."""

    relationship_type = forms.ModelChoiceField(
        queryset=RelationshipType.objects.all(),
        # TODO: provide a custom template that can show a tooltip
        # when hovering over the relationship type with the details of the relationship type
        # can be done as a completely separate MR at the end
        widget=AvailableRadioSelect(attrs={'up-validate': ''}),
        label=_('Relationship to the patient'),
    )

    form_filled = DynamicField(
        forms.BooleanField,
        label=_('The requestor filled out the request form'),
        required=lambda form: form._form_required(),  # noqa: WPS437
    )

    id_checked = forms.BooleanField(label='Requestor ID checked')

    user_type = forms.ChoiceField(
        choices=constants.USER_TYPES,
        initial=constants.UserType.NEW.name,
        widget=forms.RadioSelect(attrs={'up-validate': ''}),
    )

    first_name = DynamicField(
        forms.CharField,
        label=_('First Name'),
        required=lambda form: not form.existing_user_selected(),
    )
    last_name = DynamicField(
        forms.CharField,
        label=_('Last Name'),
        required=lambda form: not form.existing_user_selected(),
    )

    user_email = DynamicField(
        forms.CharField,
        label=_('Email Address'),
        required=lambda form: form.existing_user_selected(),
    )
    user_phone = DynamicField(
        forms.CharField,
        label=_('Phone Number'),
        initial='+1',
        validators=[validators.validate_phone_number],
        required=lambda form: form.existing_user_selected(),
    )

    def __init__(self, patient: Patient | OIEPatientData, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for card type select box and card number input box.

        Args:
            patient: a `Patient` or `OIEPatientData` instance
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        self.existing_user: Optional[Caregiver] = None

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

        self.helper.layout = Layout(
            Row(
                Column(
                    'relationship_type',
                ),
                Column(
                    Fieldset(
                        'Validation',
                        'form_filled',
                        'id_checked',
                    ),
                ),
            ),
            TabRadioSelect('user_type'),
            # empty div to be filled below depending on the chosen user type
            Div(css_class='mb-4 p-3 border-start border-end border-bottom'),
        )

        if self.existing_user_selected():
            self.helper.layout[2].append(Layout(
                Row(
                    Column('user_email', css_class='col-4'),
                    Column('user_phone', css_class='col-4'),
                    Column(InlineSubmit('search_user', 'Find User')),
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

    def existing_user_selected(self, cleaned_data: Optional[dict[str, Any]] = None) -> bool:
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

    def clean(self) -> dict[str, Any]:
        """
        Validate the form.

        Handle the "Existing user" selection by looking up the caregiver based on the inputs.

        Returns:
            the cleaned data
        """
        super().clean()
        cleaned_data = self.cleaned_data

        if self.existing_user_selected(cleaned_data):
            self._validate_existing_user()

        return cleaned_data

    def _validate_existing_user(self) -> None:
        """
        Validate the existing user selection by looking up the caregiver.

        Look up the caregiver by email **and** phone number.
        Add an error to the form if no user was found.
        """
        cleaned_data = self.cleaned_data

        # at the beginning (empty form) they are not in the cleaned data
        if 'user_email' in cleaned_data and 'user_phone' in cleaned_data:
            user_email = cleaned_data['user_email']
            user_phone = cleaned_data['user_phone']

            if user_email and user_phone:
                # ensure that we are only looking among Caregivers
                self.existing_user = Caregiver.objects.filter(  # type: ignore[assignment]
                    phone_number=user_phone,
                    email=user_email,
                ).first()

                # prevent continuing when no user was found
                if not self.existing_user:
                    self.add_error(
                        NON_FIELD_ERRORS,
                        _('No existing user found. Choose "New User" if the user cannot be found.'),
                    )

    def _form_required(self) -> bool:
        # at form initialization the selected value is only the primary key
        relationship_type = RelationshipType.objects.filter(pk=self['relationship_type'].value()).first()

        if relationship_type:
            return relationship_type.form_required

        return True


class AccessRequestConfirmForm(forms.Form):
    """This form provides a layout to confirm user password."""

    password = forms.CharField(
        widget=forms.PasswordInput(),
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


class SelectSiteForm(forms.Form):
    """This `SelectSiteForm` provides a group of buttons to choose hospital site."""

    sites = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        widget=forms.RadioSelect,
        label=_('At which hospital is the patient?'),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for site buttons.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)   # noqa: WPS204
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('sites', css_class='form-group col-md-12 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Next')),
            ),
        )


class SearchForm(forms.Form):
    """This `SearchForm` provides the layout for MRN or RAMQ type and number."""

    medical_card = forms.ChoiceField(
        widget=forms.Select(),
        choices=constants.MEDICAL_CARDS,
        label=_('Please Select A Card Type'),
    )

    medical_number = forms.CharField(
        widget=forms.TextInput(),
        label=_('Please Input The Card Number'),
    )

    site_code = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    patient_record = forms.JSONField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for card type select box and card number input box.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('medical_card', css_class='form-group col-md-3 mb-0'),
                Column('medical_number', css_class='form-group col-md-3 mb-0'),
                Column('site_code', css_class='form-group col-md-3 mb-0'),
                Column('patient_record', css_class='form-group col-md-3 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Next')),
            ),
        )
        self.oie_service = OIEService()

    def clean(self) -> None:
        """Validate medical number fields."""
        super().clean()
        medical_card_field = self.cleaned_data.get('medical_card')
        medical_number_field = self.cleaned_data.get('medical_number')
        site_code_field = self.cleaned_data.get('site_code')
        medical_number_field = str(medical_number_field or '')

        response = {}
        # Medicare Card Number (RAMQ)
        if medical_card_field == constants.MedicalCard.RAMQ.name:
            try:
                validators.validate_ramq(medical_number_field)
            except ValidationError as error_msg:
                self.add_error('medical_number', error_msg)
            else:
                # Search patient info by RAMQ.
                response = self.oie_service.find_patient_by_ramq(str(medical_number_field))
        # Medical Record Number (MRN)
        else:
            response = self.oie_service.find_patient_by_mrn(medical_number_field, str(site_code_field))

        self._handle_response(response)

    def _handle_response(self, response: Any) -> None:
        """Handle the response from OIE service.

        Args:
            response: OIE service response
        """
        # add error message to the template
        if response and response['status'] == 'error':
            self.add_error(NON_FIELD_ERRORS, response['data']['message'])
        # save patient data to the JSONfield
        elif response and response['status'] == 'success':
            self.cleaned_data['patient_record'] = response['data']


class ConfirmPatientForm(forms.Form):
    """This `ConfirmPatientForm` provides the layout for confirmation checkbox."""

    is_correct = forms.BooleanField(
        required=True,
        label=_('Correct?'),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for confirmation checkbox.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'is_correct',
            ButtonHolder(
                Submit('wizard_goto_step', _('Next')),
            ),
        )


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


class RequestorDetailsForm(forms.Form):
    """This `RequestorDetailsForm` provides a radio button to choose the relationship to the patient."""

    relationship_type = forms.ModelChoiceField(
        queryset=RelationshipType.objects.all(),
        widget=AvailableRadioSelect,
        label=_('Relationship types'),
    )

    requestor_form = forms.BooleanField(
        label=_('Has the requestor filled out the request form?'),
        widget=forms.CheckboxInput(),
        required=False,
        initial=False,
    )

    def __init__(
        self,
        ramq: Optional[str],
        mrn: str,
        site: str,
        date_of_birth: date,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the available choice of valid relationship types.

        Args:
            ramq: patient's RAMQ
            mrn: patient's MRN
            site: patient's site code
            date_of_birth: patient's date of birth
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('relationship_type', css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
            Row(
                Column('requestor_form', css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Next')),
            ),
        )
        patient = utils.get_patient_by_ramq_or_mrn(ramq, mrn, site)
        if patient:
            available_choices = utils.valid_relationship_types(patient).values_list('id', flat=True)
        else:
            available_choices = utils.search_relationship_types_by_patient_age(
                date_of_birth,
            ).values_list('id', flat=True)
        self.fields['relationship_type'].widget.available_choices = list(available_choices)

    def clean(self) -> None:
        """Validate if relationship type requested requires a form."""
        super().clean()
        type_field = self.cleaned_data.get('relationship_type')
        requestor_form_field = self.cleaned_data.get('requestor_form')

        user_select_type = RelationshipType.objects.get(name=type_field)
        if user_select_type.form_required and not requestor_form_field:
            self.add_error('requestor_form', _('Form request is required.'))


class RequestorAccountForm(forms.Form):
    """This `RequestorAccountForm` provides a select box to select existed user or new user."""

    user_type = forms.ChoiceField(
        choices=constants.TYPE_USERS,
        widget=forms.RadioSelect,
        label=_('New User or Existing User?'),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for user type select box.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('user_type', css_class='form-group col-md-3 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Next')),
            ),
        )


class ExistingUserForm(forms.Form):
    """This `ExistingUserForm` provides a layout to find existing users."""

    user_email = forms.CharField(
        widget=forms.TextInput(),
        label=_('Email Address'),
    )

    user_phone = forms.CharField(
        widget=forms.TextInput(),
        label=_('Phone Number'),
        initial='+1',
    )

    user_record = forms.JSONField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, relationship_type: RelationshipType, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for existing user form.

        Args:
            relationship_type: requestor's choice of relationship type
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('user_email', css_class='form-group col-md-3 mb-0'),
                Column('user_phone', css_class='form-group col-md-3 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Find Account')),
            ),
        )
        self.relationship_type = relationship_type

    def clean(self) -> None:
        """Validate the user selection."""
        super().clean()
        user_email_field = self.cleaned_data.get('user_email')
        user_phone_field = self.cleaned_data.get('user_phone')
        error_message = gettext(
            'Opal user was not found in your database. '
            + 'This may be an out-of-hospital account. '
            + 'Please proceed to generate a new QR code. '
            + 'Inform the user they must register at the Registration website.',
        )
        # phone and email validation
        is_email_valid = True
        is_phone_valid = True
        try:
            forms.EmailField().clean(user_email_field)
        except ValidationError as email_error_msg:
            self.add_error('user_email', email_error_msg)
            is_email_valid = False
        try:
            validators.validate_phone_number(user_phone_field)
        except ValidationError as phone_error_msg:
            self.add_error('user_phone', phone_error_msg)
            is_phone_valid = False

        if is_email_valid and is_phone_valid:
            self._set_requestor_relationship(
                user_email_field,
                user_phone_field,
                error_message,
            )

    def _set_requestor_relationship(
        self,
        user_email_field: Any,
        user_phone_field: Any,
        error_message: str,
    ) -> None:
        """
        Check if there is no 'Self' relationship related to this requestor himself/herself.

        If no, create the relationship record with the value 'Self'.
        If yes, show user details.

        Args:
            user_email_field: cleaned data for user email
            user_phone_field: cleaned data for phone number
            error_message: error message if the caregiver does not exist

        Raises:
            ValidationError: If the caregiver cannot be found.
        """
        # Search user info by both email and phone number in our django User model
        try:
            user = Caregiver.objects.get(email=user_email_field, phone_number=user_phone_field)
        except Caregiver.DoesNotExist:
            raise ValidationError(error_message)
        # Verify we cannot add an additional self role for an existing user who already has a self-relationship
        if (
            self.relationship_type.role_type == RoleType.SELF
            and Relationship.objects.filter(
                caregiver__user=user,
                type__role_type=RoleType.SELF,
            ).exists()
        ):
            raise ValidationError(gettext('This opal user already has a self-relationship with the patient.'))

        self.cleaned_data['user_record'] = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number,
        }


class ConfirmExistingUserForm(forms.Form):
    """This `ConfirmExistingUserForm` provides a layout to confirm the user information."""

    is_correct = forms.BooleanField(required=True, label=_('Correct?'))
    is_id_checked = forms.BooleanField(required=True, label=_('ID Checked?'))

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for the checkboxes.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('is_correct', css_class='form-group col-md-2 mb-0'),
                Column('is_id_checked', css_class='form-group col-md-2 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Generate Access Request')),
            ),
        )


class NewUserForm(forms.Form):
    """This `NewUserForm` provides a layout to new users."""

    first_name = forms.CharField(
        widget=forms.TextInput(),
        label=_('First Name'),
    )

    last_name = forms.CharField(
        widget=forms.TextInput(),
        label=_('Last Name'),
    )

    is_id_checked = forms.BooleanField(required=True, label=_('ID Checked?'))

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for new user form.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = False

        self.helper.layout = Layout(
            Row(
                Column('first_name'),
                Column('last_name'),
            ),
            'is_id_checked',
            ButtonHolder(
                Submit('wizard_goto_step', _('Generate QR Code')),
            ),
        )


class ConfirmPasswordForm(forms.Form):
    """This `ConfirmPasswordForm` provides a layout to confirm user password."""

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        label=_('Please confirm access to patient data by entering your password.'),
    )

    def __init__(self, authorized_user: User, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for new user form.

        Args:
            authorized_user: an authorized user
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('confirm_password', css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
            FormActions(
                CancelButton(reverse('patients:access-request')),
                Submit('wizard_goto_step', _('Confirm')),
            ),
        )
        self.authorized_user = authorized_user

    def clean(self) -> None:
        """Validate the user password."""
        super().clean()
        confirm_password = self.cleaned_data.get('confirm_password')

        if not authenticate(username=self.authorized_user.username, password=confirm_password):
            self.add_error('confirm_password', _('The password you entered is incorrect. Please try again.'))


class RelationshipAccessForm(forms.ModelForm[Relationship]):
    """Form for updating `Relationship Caregiver Access`  record."""

    first_name = forms.CharField(
        label=_('First Name'),
    )
    last_name = forms.CharField(
        label=_('Last Name'),
    )
    type = forms.ModelChoiceField(  # noqa: A003
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
        widget=forms.Textarea(attrs={'rows': '2'}),
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
            'type',
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [  # type: ignore[attr-defined]
            (choice.value, choice.label) for choice in Relationship.valid_statuses(
                RelationshipStatus(self.instance.status),
            )
        ]
        self.fields['start_date'].widget.attrs.update({   # noqa: WPS219
            'min': self.instance.patient.date_of_birth,
            'max': Relationship.calculate_end_date(
                self.instance.patient.date_of_birth,
                self.instance.type,
            ),
        })
        self.fields['end_date'].widget.attrs.update({   # noqa: WPS219
            'min': self.instance.patient.date_of_birth + timedelta(days=1),
            'max': Relationship.calculate_end_date(
                self.instance.patient.date_of_birth,
                self.instance.type,
            ),
        })

        available_choices = utils.valid_relationship_types(self.instance.patient)

        # get the RelationshipType record that corresponds to the instance
        existing_choice = RelationshipType.objects.filter(pk=self.instance.type.pk)

        # combine the instance value and with the valid relationshiptypes
        available_choices |= existing_choice

        self.fields['type'].queryset = available_choices  # type: ignore[attr-defined]

        # setting the value of caregiver first and last names
        self.fields['last_name'].initial = self.instance.caregiver.user.last_name
        self.fields['first_name'].initial = self.instance.caregiver.user.first_name

        self.helper = FormHelper(self)
        self.helper.attrs = {'novalidate': ''}
        self.helper.layout = Layout(
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
                    CancelButton('{{cancel_url}}'),
                    Submit('submit', _('Save'), css_class='btn btn-primary me-2'),
                ),
            ),
        )


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

        card_type = self.fields['card_type']
        card_type.widget.attrs.update({'up-validate': ''})
        card_type_value = self['card_type'].value()

        if card_type_value == constants.MedicalCard.MRN.name:
            self.fields['site'].required = True
        else:
            self.fields['site'].disabled = True


class ManageCaregiverAccessUserForm(forms.ModelForm[User]):
    """Form for updating a `Caregiver` object."""

    class Meta:
        model = Caregiver
        fields = [
            'first_name',
            'last_name',
        ]
