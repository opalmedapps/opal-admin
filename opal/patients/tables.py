"""Table definitions for models of the patient app."""
from typing import Dict

from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables

from .models import RelationshipType


class RelationshipTypeTable(tables.Table):
    """
    A table for relationship types.

    Defines an additional action column for action buttons.
    """

    actions = tables.TemplateColumn(
        verbose_name=_('Actions'),
        template_name='tables/action_column.html',
        orderable=False,
        extra_context={
            'urlname_update': 'patients:relationshiptype-update',
            'urlname_delete': 'patients:relationshiptype-delete',
        },
    )

    class Meta:
        model = RelationshipType
        fields = ['name', 'description', 'start_age', 'end_age', 'form_required', 'actions']
        empty_text = _('No relationship types defined.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }


class PatientTable(tables.Table):
    """
    A table for patient types.

    Dynamically change verbose name for card type field.
    """

    first_name = tables.Column()
    last_name = tables.Column()
    date_of_birth = tables.Column()
    card_number = tables.Column(verbose_name='RAMQ')

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
