"""This module provides forms for the `patients` app."""
from datetime import date, timedelta
from typing import Any

from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.urls import reverse_lazy
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Hidden, Layout, Row, Submit

from opal.core import validators
from opal.core.forms.layouts import CancelButton, Field, FormActions
from opal.core.forms.widgets import AvailableRadioSelect
from opal.services.hospital.hospital import OIEService
from opal.users.models import Caregiver, User

from . import constants
from .models import Relationship, RelationshipStatus, RelationshipType, RoleType, Site
from .utils import search_valid_relationship_types


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
        if medical_card_field == 'ramq':
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
        available_choices = search_valid_relationship_types(date_of_birth)
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
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
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
                CancelButton(reverse_lazy('patients:access-request')),
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
        queryset=RelationshipType.objects.all(),
        label=_('Relationship'),
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
        )

    def __init__(   # noqa: WPS211
        self,
        date_of_birth: date,
        relationship_type: RelationshipType,
        request_date: date,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Set the layout.

        Args:
            request_date: the date when the requestor submit the access request
            date_of_birth: patient's date of birth
            relationship_type: user selection for relationship type
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
            'min': date_of_birth,
            'max': Relationship.calculate_end_date(
                date_of_birth,
                relationship_type,
            ),
        })
        self.fields['end_date'].widget.attrs.update({   # noqa: WPS219
            'min': date_of_birth + timedelta(days=1),
            'max': Relationship.calculate_end_date(
                date_of_birth,
                relationship_type,
            ),
        })

        # setting the value of caregiver first and last names
        self.fields['last_name'].initial = self.instance.caregiver.user.last_name
        self.fields['first_name'].initial = self.instance.caregiver.user.first_name

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Field('first_name', wrapper_class='col-md-6'),
                Field('last_name', wrapper_class='col-md-6'),
                Field('type', wrapper_class='col-md-6'),
                Field('start_date', wrapper_class='col-md-6'),
                Field('status', wrapper_class='col-md-6'),
                Field('end_date', wrapper_class='col-md-6'),
                Field('reason', wrapper_class='col-md-12'),
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

    required_error = forms.Field.default_error_messages['required']

    def clean(self) -> dict[str, Any]:
        """
        Make sure that all required data is there to pass it to the filter.

        Returns:
            cleaned_data
        """
        super().clean()

        card_type = self.cleaned_data.get('card_type')
        site = self.cleaned_data.get('site')

        if card_type == constants.MedicalCard.mrn.name and not site:
            self.add_error('site', forms.ValidationError(self.required_error, 'required'))

        return self.cleaned_data
