"""This module provides forms for the `usage_statistics` app."""
from typing import Any

from django import forms
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Layout, Row

from opal.core.forms.layouts import CancelButton, FormActions, Submit

from . import constants
from .common import GroupByComponent


class UsageStatisticsExportFormMixin(forms.Form):
    """Form mixin that provides common fields and functionality for the usage statistics forms."""

    start_date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        label=_('Start Date'),
    )
    end_date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        label=_('End Date'),
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
            FormActions(
                Submit('submit', _('Download CSV')),
                Submit('submit', _('Download XLSX')),
                CancelButton(reverse('usage-statistics:reports-individual-export')),
            ),
        )

    def clean(self) -> dict[str, Any]:
        """Clean exporting usage statistics form.

        Raises:
            ValidationError: if the data is invalid.

        Returns:
            form with cleaned fields
        """
        super().clean()
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(
                    gettext('Start date cannot be later than end date.'),
                )
        return self.cleaned_data


class GroupUsageStatisticsForm(UsageStatisticsExportFormMixin):
    """Form for exporting group usage statistics data based on the provided filtering values."""

    group_by = forms.ChoiceField(
        choices=constants.TIME_INTERVAL_GROUPINGS,
        initial=GroupByComponent.DAY.name,
        label=_('Group By'),
    )
    report_type = forms.ChoiceField(
        choices=constants.GROUP_REPORT_TYPES,
        label=_('Report Type'),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super().__init__(*args, **kwargs)

        # Place the group_by and report_type fields before the action buttons
        self.helper.layout.insert(1, 'group_by')
        self.helper.layout.insert(2, 'report_type')


class IndividualUsageStatisticsForm(UsageStatisticsExportFormMixin):
    """Form for exporting individual usage statistics data based on the provided filtering values."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super().__init__(*args, **kwargs)
        start_date = self.data.get('start_date')
        end_date = self.data.get('end_date')
        self.fields['start_date'].required = bool(end_date)
        self.fields['end_date'].required = bool(start_date)

        note_text = _('If date fields are not provided, all statistical data will be extracted.')

        # Insert the note text at the top of the form
        self.helper.layout.insert(
            0,
            HTML(
                '<p class="text-muted">'
                + f'<strong>Note:</strong> {note_text}'
                + '</p>',
            ),
        )
