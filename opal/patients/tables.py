"""Table definitions for models of the patient app."""
from typing import Any

from django.db.models import QuerySet
from django.template import Context
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables
from django_tables2.columns import BoundColumn

from opal.users.models import User

from .models import HospitalPatient, Patient, Relationship, RelationshipType, RoleType


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
            kwargs: Any number of key-word arguments

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
        if record.role_type in {RoleType.SELF, RoleType.PARENT_GUARDIAN}:
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


class PatientTable(tables.Table):
    """A table for displaying patients' personal information."""

    date_of_birth = tables.DateColumn(verbose_name=_('Date of Birth'), short=False)

    mrn = tables.Column(
        verbose_name=_('MRN'),
        accessor='hospital_patients',
    )

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'mrn', 'ramq']
        empty_text = _('No patient could be found.')
        orderable = False
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }

    def render_mrn(self, value: QuerySet[HospitalPatient]) -> str:
        """Render MRN column.

        Concat list of MRN/site pairs into one string.

        E.g., "RVH: 12345, MGH: 54321"

        Args:
            value: `HospitalPatient` queryset for the MRN cell retrieved from the table data

        Returns:
            Concatenated MRN/site pairs for a given patient
        """
        # For more details:
        # https://django-tables2.readthedocs.io/en/latest/pages/custom-data.html#table-render-foo-methods
        mrn_site_list = [
            f'{hospital_patient.site.code}: {hospital_patient.mrn}' for hospital_patient in value.all()
        ]

        return ', '.join(str(mnr_value) for mnr_value in mrn_site_list)


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
        accessor='type',
    )

    start_date = tables.DateColumn(
        verbose_name=_('Start Date'),
    )

    end_date = tables.DateColumn(
        verbose_name=_('End Date'),
    )

    status = tables.Column(
        verbose_name=_('Status'),
        attrs={
            'th': {'align': 'center'},
        },
    )

    actions = tables.TemplateColumn(
        verbose_name=_('Actions'),
        # TODO: use action_column.html template once the update/delete pages are implemented
        template_name='tables/edit_pencil_icon.html',
        attrs={
            'td': {'align': 'center'},
        },
        orderable=False,
        extra_context={
            # TODO: update urlname_delete and urlname_update values once the corresponding pages are implemented
            'urlname_delete': '',
            'urlname_update': '',
        },
    )

    class Meta:
        model = Relationship
        fields = [
            'first_name',
            'last_name',
            'relationship_type',
            'start_date',
            'end_date',
            'status',
            'actions',
        ]
        empty_text = _('No caregiver could be found.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }
