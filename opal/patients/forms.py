"""This module provides forms for Patients."""
from datetime import date, datetime
from typing import Any, Dict, Optional, Set, Union

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit

from opal.core import validators
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData
from opal.users.models import Caregiver

from . import constants
from .models import CaregiverProfile, Patient, Relationship, RelationshipType, Site


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


def _patient_data() -> OIEPatientData:
    """
    Return the fake patient data pretended to get from OIE calling.

    Returns:
        patient data structure in 'OIEPatientData'
    """
    return OIEPatientData(
        date_of_birth=datetime.strptime('1984-05-09 09:20:30', '%Y-%m-%d %H:%M:%S'),
        first_name='Marge',
        last_name='Simpson',
        sex='F',
        alias='',
        ramq='MARG99991313',
        ramq_expiration=datetime.strptime('2024-01-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MCH',
                mrn='9999994',
                active=True,
            ),
            OIEMRNData(
                site='RVH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def _find_patient_by_mrn_fail(mrn: str, site: str) -> Any:
    """
    Search patient info by MRN code.

    Args:
        mrn: Medical Record Number (MRN) code (e.g., 9999993)
        site: site code (e.g., MGH)

    Returns:
        patient info or an error in JSON format
    """
    return {
        'status': 'error',
        'data': {
            'message': 'Provided MRN or site is invalid.',
            'responseData': {'status': 'error', 'data': None},
        },
    }


def _find_patient_by_mrn_success(mrn: str, site: str) -> Any:
    """
    Search patient info by MRN code.

    Args:
        mrn: Medical Record Number (MRN) code (e.g., 9999993)
        site: site code (e.g., MGH)

    Returns:
        patient info or an error in JSON format
    """
    return {
        'status': 'success',
        'data': _patient_data(),
    }


def _find_patient_by_ramq(ramq: str) -> Any:
    """
    Search patient info by RAMQ code.

    Args:
        ramq (str): RAMQ code

    Returns:
        patient info or an error in JSON format
    """
    return {
        'status': 'success',
        'data': _patient_data(),
    }


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

    def clean(self) -> None:
        """Validate medical number fields."""
        super().clean()
        medical_card_field = self.cleaned_data.get('medical_card')
        medical_number_field = self.cleaned_data.get('medical_number')
        site_code_field = self.cleaned_data.get('site_code')

        response = {}
        # Medicare Card Number (RAMQ)
        if medical_card_field == 'ramq':
            try:
                validators.validate_ramq(medical_number_field)
            except ValidationError as error_msg:
                self.add_error('medical_number', error_msg)
            else:
                # Search patient info by RAMQ.
                response = _find_patient_by_ramq(str(medical_number_field))
        # Medical Record Number (MRN)
        else:
            response = _find_patient_by_mrn_success(str(medical_number_field), str(site_code_field))

        # add error message to the tempate
        if response and response['status'] == 'error':
            self.add_error('medical_number', response['data']['message'])
        # save patient data to the JSONfield
        elif response and response['status'] == 'success':
            self.cleaned_data['patient_record'] = response['data']  # type: ignore[index]


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


class AvailableRadioSelect(forms.RadioSelect):
    """
    Subclass of Django's select widget that allows disabling options.

    Taken inspiration from:
        * https://stackoverflow.com/questions/673199/disabled-option-for-choicefield-django/50109362#50109362
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the '_available_choices'.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        self._available_choices: list[int] = []
        super().__init__(*args, **kwargs)

    @property
    def available_choices(self) -> list[int]:
        """
        Get _available_choices.

        Returns:
            the list for _available_choices.
        """
        return self._available_choices

    @available_choices.setter
    def available_choices(self, other: list[int]) -> None:
        """
        Set _available_choices.

        Args:
            other: the new value _available_choices
        """
        self._available_choices = other

    def create_option(  # noqa: WPS211
        self,
        name: str,
        value: Any,
        label: Union[int, str],
        selected: Union[Set[str], bool],
        index: int,
        subindex: Optional[int] = None,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initialize the '_available_choices'.

        Args:
            name: option name
            value: option value
            label: option label
            selected: selected option
            index: option index
            subindex: option subindex
            attrs: option attributes

        Returns:
            the dict for _available_choices.
        """
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs,
        )
        if value not in self.available_choices:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict


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

    def __init__(self, date_of_birth: date, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for card type select box and card number input box.

        Args:
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
        self.age = Patient.calculate_age(date_of_birth=date_of_birth)
        available_choices = RelationshipType.objects.filter_by_patient_age(
            patient_age=self.age,
        ).values_list('id', flat=True)
        self.fields['relationship_type'].widget.available_choices = available_choices

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
    )

    user_record = forms.JSONField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(
        self,
        relationship_type: RelationshipType,
        patient_record: OIEPatientData,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the layout for existing user form.

        Args:
            relationship_type: caregiver relationship type
            patient_record: patient record retrieved from OIE service
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
        self.patient_record = patient_record

    def clean(self) -> None:
        """Validate the user selection."""
        super().clean()
        user_email_field = self.cleaned_data.get('user_email')
        user_phone_field = self.cleaned_data.get('user_phone')
        error_message = _(
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

        self._set_requestor_relationship(
            is_email_valid,
            is_phone_valid,
            user_email_field,
            user_phone_field,
            error_message,
        )

    def _set_requestor_relationship(    # noqa: WPS211
        self,
        is_email_valid: bool,
        is_phone_valid: bool,
        user_email_field: Any,
        user_phone_field: Any,
        error_message: str,
    ) -> None:
        """
        Check if there is no 'Self' relationship related to this requestor himself/herself.

        If no, create the relationship record with the value 'Self'.
        If yes, show user details.

        Args:
            is_email_valid: email address is valid by default
            is_phone_valid: phone number is valid by default
            user_email_field: cleaned data for user email
            user_phone_field: cleaned data for phone number
            error_message: error message if the caregiver does not exist

        Raises:
            ValidationError: If the caregiver cannot be found.
        """
        # Search user info by both email and phone number in our django User model
        if is_email_valid and is_phone_valid:
            try:
                user = Caregiver.objects.get(email=user_email_field, phone_number=user_phone_field)
            except Caregiver.DoesNotExist:
                raise ValidationError(error_message)

        # Check if there is no 'Self' relationship related to this requestor himself/herself
        # TODO: we'll need to change the 'Self' once ticket QSCCD-645 is done.
        relationships = Relationship.objects.get_relationship_by_patient_caregiver(
            'Self',
            user.first_name,
            user.last_name,
            user.id,
            self.patient_record.ramq,
        )
        # If no, create the relationship record with the value 'Self'
        # TODO: we'll need to change the 'Self' once ticket QSCCD-645 is done
        # TODO: I'll refactor this part based on new mockup to make it happens after generating access request
        if not relationships and str(self.relationship_type) == 'Self':
            Relationship.objects.create(
                patient=Patient.objects.get(ramq=self.patient_record.ramq),
                caregiver=CaregiverProfile.objects.get(user_id=user.id),
                type=self.relationship_type,
                reason=_('Create self relationship for patient'),
                request_date=date.today(),
                start_date=date.today(),
            )
        # If yes, show user details
        elif relationships:
            self.cleaned_data['user_record'] = {  # type: ignore[index]
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
