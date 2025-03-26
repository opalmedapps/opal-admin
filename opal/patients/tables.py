"""Table definitions for models of the patient app."""
from typing import Any

from django.template import Context
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables
from django_tables2.columns import BoundColumn

from .models import Relationship, RelationshipType, RoleType


# Adjusting context depending on record content:
# https://stackoverflow.com/questions/53582717/django-tables2-adding-template-column-which-content-depends-on-condition
class RelationshipTypeTemplateColumn(tables.TemplateColumn):
    """A customized template column overriding the default behaviour."""

    def render(  # noqa: WPS211
        self,
        record: RelationshipType,
        table: Any,
        value: None,
        bound_column: BoundColumn,
        **kwargs: Any,
    ) -> tables.TemplateColumn:
        """Override the rendering method to remove delete option in restricted role types.

        Args:
            record: The RelationshipType instance
            table: The RelationshipTypeTable instance
            value: value from `record` that corresponds to the current column
            bound_column: The column being rendered
            kwargs: Any number of key-word arguements

        Returns:
            TemplateColumn: the renderable content for the column
        """
        context = getattr(table, 'context', Context())
        additional_context = {
            'default': bound_column.default,
            'column': bound_column,
            'record': record,
            'value': value,
            'row_counter': kwargs['bound_row'].row_counter,
        }

        # Remove the deletion button for restricted types
        if record.role_type in {RoleType.SELF, RoleType.PARENTGUARDIAN}:
            self.extra_context = {'urlname_update': 'patients:relationshiptype-update'}
        else:
            self.extra_context = {
                'urlname_update': 'patients:relationshiptype-update',
                'urlname_delete': 'patients:relationshiptype-delete',
            }
        additional_context.update(self.extra_context)
        with context.update(self.extra_context):
            return super().render(record, table, value, bound_column, **kwargs)


class RelationshipTypeTable(tables.Table):
    """
    A table for relationship types.

    Defines an additional action column for action buttons.
    """

    actions = RelationshipTypeTemplateColumn(
        verbose_name=_('Actions'),
        template_name='tables/action_column.html',
        orderable=False,
    )

    class Meta:
        model = RelationshipType
        fields = [
            'name',
            'description',
            'start_age',
            'end_age',
            'role_type',
            'form_required',
            'can_answer_questionnaire',
            'actions',
        ]
        empty_text = _('No relationship types defined.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }


class PendingRelationshipTable(tables.Table):
    """
    A table for relationships.

    Defines an additional action column for action buttons.
    """

    actions = tables.TemplateColumn(
        verbose_name=_('Actions'),
        template_name='tables/action_column.html',
        orderable=False,
        extra_context={
            'urlname_update': 'patients:relationships-pending-update',
        },
    )
    type = tables.Column(  # noqa: A003
        verbose_name=_('Relationship'),
    )
    request_date = tables.Column(
        verbose_name=_('Pending Since'),
    )

    class Meta:
        model = Relationship
        fields = ['caregiver', 'type', 'patient', 'request_date', 'actions']
        empty_text = _('No caregiver pending access requests.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }


class RelationshipPatientTable(tables.Table):
    """A table for displaying patients' personal information."""

    first_name = tables.Column(
        verbose_name=_('First Name'),
        accessor='patient__first_name',
    )

    last_name = tables.Column(
        verbose_name=_('Last Name'),
        accessor='patient__last_name',
    )

    date_of_birth = tables.DateColumn(
        verbose_name=_('Date of Birth'),
        accessor='patient__date_of_birth',
    )

    ramq = tables.Column(
        verbose_name=_('RAMQ'),
        accessor='patient__ramq',
    )

    class Meta:
        model = Relationship
        fields = ['first_name', 'last_name', 'date_of_birth', 'ramq']
        empty_text = _('No patient found.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }


class RelationshipCaregiverTable(tables.Table):
    """A table for displaying caregivers' personal information."""

    first_name = tables.Column(
        verbose_name=_('First Name'),
        accessor='caregiver__user__first_name',
    )

    last_name = tables.Column(
        verbose_name=_('Last Name'),
        accessor='caregiver__user__last_name',
    )

    relationship_type = tables.Column(
        verbose_name=_('Relationship'),
    )

    start_date = tables.DateColumn(
        verbose_name=_('Start Date'),
    )

    end_date = tables.DateColumn(
        verbose_name=_('End Date'),
    )

    status = tables.Column(
        verbose_name=_('Status'),
    )

    actions = tables.Column(
        verbose_name=_('Actions'),
        orderable=False,
    )

    class Meta:
        model = Relationship
        fields = ['first_name', 'last_name', 'relationship_type', 'start_date', 'end_date', 'status', 'actions']
        empty_text = _('No caregivers.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }
