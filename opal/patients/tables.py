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
        fields = [
            'name',
            'description',
            'start_age',
            'end_age',
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
