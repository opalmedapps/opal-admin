"""This module provides filters for `patients` app."""
from typing import Any

from django.utils.translation import gettext_lazy as _

import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit

from opal.hospital_settings.models import Site

from . import constants
from .models import Patient


class ManageCaregiverAccessFilter(django_filters.FilterSet):
    """
    This `ManageCaregiverAccessFilter` declares filters for the `Search Patient Access` page.

    The filter initializes a custom `Form` using crispy's layout.
    """

    # This field does not perform queryset filtering but defines how the filter should work
    # E.g., sets if the queryset should be filtered using MRN or RAMQ number
    medical_card_type = django_filters.ChoiceFilter(
        choices=constants.MEDICAL_CARDS,
        label=_('Card Type'),
        required=True,
    )

    site = django_filters.ModelChoiceFilter(
        field_name='hospital_patients__site',
        queryset=Site.objects.all(),
        label='Site',
    )

    medical_number = django_filters.CharFilter(
        field_name='ramq',
        label='Medical Number',
        required=True,
    )

    class Meta:
        model = Patient
        fields = ['site', 'medical_number']

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the filter and set the form layout for the search area of the "Manage Caregiver Access" page.

        The form contains fields for the medical card type (MRN or RAMQ), sites' codes, and medical number.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        self.form.helper = FormHelper(self.form)
        self.form.helper.form_tag = False
        self.form.helper.disable_csrf = True

        self.form.helper.layout = Layout(
            Row(
                Column('medical_card_type', css_class='form-group col-md-6 mb-0'),
                Column('site', css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
            Row(
                Column('medical_number', css_class='form-group col-md-6 mb-0'),
                Submit('search', _('Search'), css_class='form-group col-md-6 mb-4 mt-4 btn btn-primary'),
                css_class='form-row',
            ),
        )

    def filter_queryset(self, queryset: Patient) -> Any:
        """
        Perform custom queryset filtering based on the underlying form's `cleaned_data`.

        The method removes 'medical_card_type' field since the field does not perform queryset filtering.

        Args:
            queryset: `Patient` queryset that is being filtered based on the given fields' values

        Returns:
            Filtered `Patient` queryset
        """
        # Remove 'medical_card_type' field from the form since this field does not perform queryset filtering
        card_type = self.form.cleaned_data.pop('medical_card_type')
        # Set medical_number's 'field_name' by which the filtering will be performed
        if card_type == constants.MedicalCard.mrn.name.lower():
            self.filters['medical_number'].field_name = 'hospital_patients__mrn'
        else:
            self.filters['medical_number'].field_name = 'ramq'
        return super().filter_queryset(queryset)
