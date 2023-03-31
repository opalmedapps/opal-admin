"""This module provides filters for `patients` app."""
from typing import Any

from django import forms
from django.db.models import QuerySet
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout

from opal.core.form_layouts import InlineReset, InlineSubmit
from opal.hospital_settings.models import Site

from . import constants
from .models import Relationship


class ManageCaregiverAccessForm(forms.Form):
    required_error = forms.Field.default_error_messages['required']

    def clean(self) -> dict[str, Any]:
        super().clean()

        card_type = self.cleaned_data.get('card_type')
        site = self.cleaned_data.get('site')

        if card_type == constants.MedicalCard.mrn.name and not site:
            self.add_error('site', forms.ValidationError(self.required_error, 'required'))

        return self.cleaned_data


class ManageCaregiverAccessFilter(django_filters.FilterSet):
    """
    This `ManageCaregiverAccessFilter` declares filters for the `Search Patient Access` page.

    The filter initializes a custom `Form` using crispy's layout.
    """

    # This field does not perform queryset filtering but defines how the filter should work
    # E.g., defines if the queryset should be filtered by the patient's MRN or RAMQ number
    card_type = django_filters.ChoiceFilter(
        choices=constants.MEDICAL_CARDS,
        label=_('Card Type'),
        required=True,
        empty_label=_('Choose...'),
    )

    site = django_filters.ModelChoiceFilter(
        field_name='patient__hospital_patients__site',
        queryset=Site.objects.all(),
        label=_('Hospital'),
        empty_label=_('Choose...'),
        # help_text=_('Required when searching by MRN'),
    )

    medical_number = django_filters.CharFilter(
        label=_('Identification Number'),
        required=True,
    )

    class Meta:
        model = Relationship
        form = ManageCaregiverAccessForm
        fields = ['card_type', 'site', 'medical_number']

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the filter and set the form layout for the search area of the "Manage Caregiver Access" page.

        The form contains fields for the medical card type (MRN or RAMQ), sites' codes, and medical number.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        self.form.helper = FormHelper()
        self.form.helper.form_class = 'form-inline row row-cols-lg-auto g-3 align-items-baseline'
        self.form.helper.attrs = {'novalidate': ''}
        self.form.helper.form_method = 'GET'
        self.form.helper.disable_csrf = True
        self.form.helper.layout = Layout(
            Column('card_type'),
            Column('site'),
            Column('medical_number'),
            Column(InlineSubmit('', gettext('Search'))),
            Column(InlineReset()),
        )

        medical_number_field = self.form.fields['medical_number']
        medical_number_field.widget.attrs['placeholder'] = medical_number_field.label

    def filter_queryset(self, queryset: QuerySet[Relationship]) -> Any:
        """
        Perform custom queryset filtering based on the underlying form's `cleaned_data`.

        The method removes 'card_type' field since the field does not perform queryset filtering.

        Args:
            queryset: `Patient` queryset that is being filtered based on the given fields' values

        Returns:
            Filtered `Patient` queryset
        """
        # Remove 'medical_card_type' field from the form since this field does not perform queryset filtering
        card_type = self.form.cleaned_data.pop('card_type')

        # Set medical_number's 'field_name' by which the filtering will be performed
        if card_type == constants.MedicalCard.mrn.name:
            self.filters['medical_number'].field_name = 'patient__hospital_patients__mrn'
        else:
            self.filters['medical_number'].field_name = 'patient__ramq'

        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)

        return super().filter_queryset(queryset)
