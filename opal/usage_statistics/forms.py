"""This module provides forms for the `usage_statistics` app."""
from typing import Any

from django import forms
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Field, Layout, Row

from opal.core.forms.layouts import CancelButton, FormActions, Submit


class UsageStatisticsExportForm(forms.Form):
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
        required=True,
        choices=(
            ('BY_DAY', _('Day')),
            ('BY_MONTH', _('Month')),
            ('BY_YEAR', _('Year')),
        ),
        initial='BY_YEAR',
        label=_('Group By'),
    )
    report_type = forms.MultipleChoiceField(
        choices=(
            ('summary_report', _('Grouped registration codes, caregivers, patients, device identifiers')),
            ('data_received_report', _('Grouped patients received data')),
            ('app_activity_report', _('Grouped patient/user app activity')),
            ('individual_patient_report', _('Individual reports for Labs, Logins, Demographics & Diagnoses')),
        ),
        widget=forms.widgets.CheckboxSelectMultiple,
        label='',
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

        report_type_label = gettext('Report Type*')
        self.helper.layout = Layout(
            Row(
                Column('start_date', css_class='col-6'),
                Column('end_date', css_class='col-6'),
            ),
            'group_by',
            Field(
                HTML(f'<label for="id_report_type" class="form-label requiredField">{report_type_label}</label>'),
                'report_type',
            ),
            FormActions(
                Submit('submit', _('Download csv')),
                Submit('submit', _('Download xlsx')),
                CancelButton(reverse('usage-statistics:data-export')),
            ),
        )
