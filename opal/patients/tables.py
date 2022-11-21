"""Table definitions for models of the patient app."""
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables

from opal.users.models import User

from .models import Patient, Relationship, RelationshipType


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
    """A table for patient types."""

    date_of_birth = tables.DateColumn(verbose_name=_('Date of Birth'), short=False)

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'ramq']
        empty_text = _('No patient could be found.')
        orderable = False
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }


class ExistingUserTable(tables.Table):
    """A table for existing user information."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        empty_text = _('No existing user could be found.')
        orderable = False
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

    actions = tables.Column(
        verbose_name=_('Actions'),
        orderable=False,
    )
    type = tables.Column(  # noqa: A003
        verbose_name=_('Relationship'),
    )
    request_date = tables.Column(
        verbose_name=_('Pending Since'),
    )

    class Meta:
        model = Relationship
        fields = ['caregiver', 'type', 'patient', 'request_date', 'form_required', 'actions']
        empty_text = _('No caregiver pending access requests.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }
