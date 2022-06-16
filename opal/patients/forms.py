"""This module provides forms for Patients."""
from datetime import date, datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from opal.patients.models import RelationshipType


class RelationshipTypeForm(forms.Form):
    """This `RelationshipTypeForm` provides an radio button to choose relationship to the patient."""

    types = forms.ModelChoiceField(
        queryset=RelationshipType.objects.all(),
        widget=forms.RadioSelect(),
        label=_('Caregiver relationship type'),
    )
    requestor_form = forms.BooleanField(
        label=_('Has the requestor filled out the request form?'),
        widget=forms.CheckboxInput(attrs={'onChange': 'this.form.submit();'}),
        required=True,
        initial=False,
    )

    def __init__(self, date_of_birth: str) -> None:
        """
        Initialize default type.

        Args:
            date_of_birth: patient's date of birth.
        """
        super().__init__()
        self.age = calculate_age(datetime.strptime(date_of_birth, '%Y-%m-%d %H:%M:%S'))
        self.fields['types'].queryset = RelationshipType.objects.filter_by_patient_age(patient_age=self.age)


def calculate_age(birthdate: date) -> int:
    """
    Return the age based on the given date of birth.

    Args:
        birthdate: pass the given date of birth.

    Returns:
        the age based on the given date of birth.
    """
    # Get today's date object
    today = date.today()
    # A bool that represents if today's day/month precedes the birth day/month
    one_or_zero = ((today.month, today.day) < (birthdate.month, birthdate.day))
    # Calculate the difference in years from the date object's components
    year_difference = today.year - birthdate.year
    # The difference in years is not enough.
    # To get it right, subtract 1 or 0 based on if today precedes the birthdate's month/day.
    return year_difference - one_or_zero


class MedicalCardForm(forms.Form):
    """This `MedicalCardForm` provide layout for MRN or RAMQ type and number."""

    medical_card_types = [
        ('mrn', 'MRN'),
        ('ramq', 'RAMQ'),
    ]

    medical_type = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        choices=medical_card_types,
        initial='mrn',
    )
    medical_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    site_code = forms.CharField(
        widget=forms.HiddenInput(),
    )

    def __init__(self, mrn: str, sitecode: str) -> None:
        """
        Initialize value for medical number and site code.

        Args:
            mrn: patient's MRN number.
            sitecode: the site code.
        """
        super().__init__()
        self.fields['medical_number'].initial = mrn
        self.fields['site_code'].initial = sitecode
