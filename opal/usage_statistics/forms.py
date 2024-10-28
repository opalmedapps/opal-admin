"""This module provides forms for the `usage_statistics` app."""
from typing import Any

from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row

from opal.core.forms.layouts import CancelButton, FormActions, Submit
from opal.patients.forms import AccessRequestSearchPatientForm


class UsageStatisticsExportForm(AccessRequestSearchPatientForm):
    """Form for exporting usage statistics data based on the provided filtering values."""

    start_date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        label=_('Start Date'),
    )
    end_date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        label=_('End Date'),
    )
    group_by = forms.ChoiceField(
        choices=(
            ('BY_DATE', _('Date')),
            ('BY_MONTH', _('Month')),
            ('BY_YEAR', _('Year')),
        ),
        initial='BY_YEAR',
        label=_('Group By'),
    )
    summary_report = forms.BooleanField(
        required=False,
        label=_('Grouped registration codes, caregivers, patients, device identifiers'),
    )
    data_received_report = forms.BooleanField(
        required=False,
        label=_('Grouped patients received data'),
    )
    app_activity_report = forms.BooleanField(
        required=False,
        label=_('Grouped patient/user app activity'),
    )
    individual_patient_report = forms.BooleanField(
        required=False,
        label=_('Individual reports for Labs, Logins, Demographics & Diagnoses'),
    )
    all_reports = forms.BooleanField(
        required=False,
        label=_('All statistic reports'),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Row(
                Column('start_date', css_class='col-6'),
                Column('end_date', css_class='col-6'),
            ),
            'group_by',
            'summary_report',
            'data_received_report',
            'app_activity_report',
            'individual_patient_report',
            'all_reports',
            Row(
                Column('card_type', css_class='col-4'),
                Column('medical_number', css_class='col-3'),
                Column('site', css_class='col-5'),
            ),
            FormActions(
                Submit('submit', _('Download csv')),
                Submit('submit', _('Download xlsx')),
                CancelButton(reverse('usage-statistics:data-export')),
            ),
        )
