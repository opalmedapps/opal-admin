"""Table definitions for models of the patient app."""
from typing import Any

from django.db.models import QuerySet
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables

from opal.services.hospital.hospital_data import OIEMRNData
from opal.users.models import User

from .models import HospitalPatient, Patient, Relationship, RelationshipStatus, RelationshipType, RoleType


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

    def render_actions(
        self,
        record: RelationshipType,
        column: tables.TemplateColumn,
        *args: Any,
        **kwargs: Any,
    ) -> SafeString:
        """
        Render the actions column.

        Append the delete URL name to the `extra_context` if the record has a role type of `CAREGIVER`.

        Args:
            record: the current relationship type
            column: the current column
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the rendered column HTML
        """
        if record.role_type == RoleType.CAREGIVER:
            column.extra_context.update({
                'urlname_delete': 'patients:relationshiptype-delete',
            })

        return column.render(record, *args, **kwargs)  # type: ignore[no-any-return]


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

        return ', '.join(str(mrn_value) for mrn_value in mrn_site_list)


class ExistingUserTable(tables.Table):
    """A table for existing user information."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        empty_text = _('No existing user could be found.')
        orderable = False


class PendingRelationshipTable(tables.Table):
    """
    A table for relationships.

    Defines an additional action column for action buttons.
    """

    actions = tables.TemplateColumn(
        verbose_name=_('Actions'),
        template_name='tables/action_column.html',
        orderable=False,
    )
    type = tables.Column(  # noqa: A003
        verbose_name=_('Relationship'),
    )
    status = tables.Column(
        verbose_name=Relationship._meta.get_field('status').verbose_name,  # noqa: WPS437
        order_by='request_date',
    )

    def render_status(self, value: str, record: Relationship) -> str:
        """
        Render the status of the relationship.

        For a pending status, the number of days since the relationship was requested is appended.
        For example: "Pending (123 days)"

        Args:
            value: the relationship status label
            record: the relationship

        Returns:
            the status label, suffixed
        """
        status_value = value

        if value == RelationshipStatus.PENDING.label:
            today = timezone.now().date()
            status_since = today - record.request_date
            pending_since_text = _('{days} days'.format(days=status_since.days))
            status_value = f'{value} ({pending_since_text})'

        return status_value

    def render_actions(
        self,
        record: Relationship,
        column: tables.TemplateColumn,
        *args: Any,
        **kwargs: Any,
    ) -> SafeString:
        """
        Render the actions column.

        Change the edit URL name in the `extra_context` if the record status is expired to make it readonly.

        Args:
            record: the current relationship
            column: the current column
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the rendered column HTML
        """
        if record.status == RelationshipStatus.EXPIRED:
            column.extra_context.update({
                'urlname_view': 'patients:relationships-pending-readonly',
                'urlname_update': '',
            })
        else:
            column.extra_context.update({
                'urlname_view': '',
                'urlname_update': 'patients:relationships-pending-update',
            })

        return column.render(record, *args, **kwargs)  # type: ignore[no-any-return]

    class Meta:
        model = Relationship
        fields = ['patient', 'caregiver', 'type', 'status', 'actions']
        empty_text = _('No caregiver requests found.')


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
        # TODO: use action_column.html template once the delete pages are implemented
        template_name='tables/action_column.html',
        attrs={
            'td': {'align': 'center'},
        },
        orderable=False,
        extra_context={
            # TODO: update urlname_delete values once the corresponding pages are implemented
            'urlname_update': 'patients:relationships-pending-update',
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


class ConfirmPatientDetailsTable(tables.Table):
    """Custom table for confirmation of patient data given an OIE data object.

    The goal of this table is to render data in the same way as the existing `PatientTable`
    A new table is required because the existing table is rendered using a patient queryset in
    a situation where we know the patient already exists, however this is not the case for the registration
    workflow where sometimes a patient may not exist already. As such, the rendering below is defined.
    """

    first_name = tables.Column(verbose_name=_('First Name'))
    last_name = tables.Column(verbose_name=_('Last Name'))
    date_of_birth = tables.DateColumn(verbose_name=_('Date of Birth'), short=False)
    mrns = tables.Column(verbose_name=_('MRN'))
    ramq = tables.Column(verbose_name=_('RAMQ Number'))

    class Meta:
        empty_text = _('No patient could be found.')
        orderable = False

    def render_mrns(self, value: list[OIEMRNData]) -> str:
        """Render MRN column by pulling from the custom OIE data object.

        Args:
            value: OIEMRNData list

        Returns:
            Concatenated MRN/site pairs for a given patient
        """
        mrn_site_list = [
            f'{hospital_patient.site}: {hospital_patient.mrn}' for hospital_patient in value
        ]
        return ', '.join(str(mrn_value) for mrn_value in mrn_site_list)
