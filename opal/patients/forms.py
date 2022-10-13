"""This module provides forms for Patients."""
import json
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit

from opal.core import validators

from . import constants
from .models import Site


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
        super().__init__(*args, **kwargs)
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


def _patient_data() -> Any:
    """
    Return the fake patient data pretended to get from OIE calling.

    Returns:
        patient data in JSON format
    """
    return {
        'dateOfBirth': '1953-01-01 09:20:30',
        'firstName': 'SANDRA',
        'lastName': 'TESTMUSEMGHPROD',
        'sex': 'F',
        'alias': '',
        'ramq': 'TESS53510111',
        'ramqExpiration': '2018-01-31 23:59:59',
        'mrns': [
            {
                'site': 'MGH',
                'mrn': '9999993',
                'active': True,
            },
            {
                'site': 'MCH',
                'mrn': '9999994',
                'active': True,
            },
            {
                'site': 'RVH',
                'mrn': '9999993',
                'active': True,
            },
        ],
    }


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
        'data': {
            'first_name': _patient_data()['firstName'],
            'last_name': _patient_data()['lastName'],
            'date_of_birth': _patient_data()['dateOfBirth'],
            'ramq': _patient_data()['ramq'],
            'mrns': _patient_data()['mrns'],
        },
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
        'data': {
            'first_name': _patient_data()['firstName'],
            'last_name': _patient_data()['lastName'],
            'date_of_birth': _patient_data()['dateOfBirth'],
            'ramq': _patient_data()['ramq'],
            'mrns': _patient_data()['mrns'],
        },
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
            args: additional argumentssle
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
            self.cleaned_data['patient_record'] = json.dumps(response['data'])  # type: ignore[index]


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
                Submit('wizard_goto_step', _('Generate QR Code')),
            ),
        )
