"""Table definitions for models of the patient app."""
from typing import Dict

from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables


class PatientTable(tables.Table):
    """
    A table for patient types.

    Defines an additional action column for action buttons.
    """

    first_name = tables.Column()
    last_name = tables.Column()
    date_of_birth = tables.Column()
    actions = tables.TemplateColumn(
        verbose_name=_('Correct'),
        template_name='patients/patient/action_column.html',
    )

    class Meta:
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }

    def render_date_of_birth(self, value: str, record: Dict) -> str:  # noqa: WPS110
        """
        Return a format string with a hidden value.

        Args:
            value: the date of birth.
            record: table fields dict.

        Returns:
            a format string with a hidden value.
        """
        return format_html('{0}<input type="hidden" name="dateOfBirth" value="{1}">', value, record['date_of_birth'])
