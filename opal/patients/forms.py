"""This module provides `ModelForm` for the `patients` using crispy forms."""

from typing import Any

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout

from .models import Relationship


class RelationshipPendingAccessForm(forms.ModelForm):
    """Form for updating an `Pending Relationship Access` object."""

    patient = forms.CharField()
    caregiver = forms.CharField()
    date_of_birth = forms.DateField()
    patient_identification_number = forms.CharField()
    start_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Relationship
        fields = (
            'patient',
            'caregiver',
            'type',
            'date_of_birth',
            'patient_identification_number',
            'start_date',
            'end_date',
            'status',
            'reason',
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        kwargs['initial']['date_of_birth'] = str(kwargs['instance'].patient.date_of_birth)  # noqa: WPS204
        kwargs['initial']['patient_identification_number'] = kwargs['instance'].patient.ramq
        kwargs['initial']['patient'] = '{first} {last}'.format(
            first=kwargs['instance'].patient.first_name,
            last=kwargs['instance'].patient.last_name,
        )
        kwargs['initial']['caregiver'] = kwargs['instance'].caregiver
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Field('patient', disabled=True, css_class='form-group col-md-12 mb-0'),
            Field('caregiver', disabled=True, css_class='form-group col-md-12 mb-0'),
            Field('patient_identification_number', readonly=True),
            Field('date_of_birth', readonly=True),
            'start_date',
            'end_date',
            'status',
            'reason',
            'date',
        )
