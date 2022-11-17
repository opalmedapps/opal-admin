"""This module provides `ModelForm` for the `patients` using crispy forms."""

from typing import Any

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout

from .models import Relationship


class RelationshipPendingAccessForm(forms.ModelForm):
    """Form for updating an `Pending Relationship Access` object."""

    date_of_birth = forms.DateField(widget=forms.DateInput(format='%Y%m%d'))  # noqa: WPS323
    patient_identification_number = forms.CharField()
    start_date = forms.DateField(widget=forms.DateInput(format='%Y%m%d'))  # noqa: WPS323
    end_date = forms.DateField(widget=forms.DateInput(format='%Y%m%d'))  # noqa: WPS323

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
        kwargs['initial']['date_of_birth'] = str(kwargs['instance'].patient.date_of_birth)
        kwargs['initial']['patient_identification_number'] = kwargs['instance'].patient.ramq
        kwargs['initial']['start_date'] = str(kwargs['instance'].start_date)
        kwargs['initial']['end_date'] = str(kwargs['instance'].end_date)
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
        )
