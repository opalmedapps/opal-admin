"""This module provides filters for `patients` app."""
from typing import Any

from django.db.models import QuerySet
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout

from opal.hospital_settings.models import Site

from ..core.forms.layouts import InlineReset, InlineSubmit
from . import constants
from .forms import ManageCaregiverAccessForm
from .models import Relationship


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
            Column(InlineSubmit('', gettext('Search Specific Patient'))),
            Column(InlineReset()),
        )

        medical_number_field = self.form.fields['medical_number']
        medical_number_field.widget.attrs['placeholder'] = medical_number_field.label

    def filter_queryset(self, queryset: QuerySet[Relationship]) -> QuerySet[Relationship]:
        """
        Perform custom queryset filtering based on the underlying form's `cleaned_data`.

        The method removes 'card_type' field since the field does not perform queryset filtering.

        Args:
            queryset: `Patient` queryset that is being filtered based on the given fields' values

        Returns:
            Filtered `Relationship` queryset
        """
        # Remove 'medical_card_type' field from the form since this field does not perform queryset filtering
        card_type = self.form.cleaned_data.pop('card_type')
        site_obj = self.form.cleaned_data.pop('site')
        medical_number = self.form.cleaned_data.pop('medical_number')

        print(type(site_obj))

        if card_type == constants.MedicalCard.mrn.name:
            queryset = queryset.filter(
                patient__hospital_patients__site__name=site_obj.name,
                patient__hospital_patients__mrn=medical_number,
            )
        else:
            queryset = queryset.filter(
                patient__ramq=medical_number,
            )

        return queryset
