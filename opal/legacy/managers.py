"""
Module providing legacy model managers to provide the interface through which Legacy DB query operations.

Each manager in this module should be prefixed with `Legacy`

Module also provide mixin classes to make the code reusable.

'A mixin is a class that provides method implementations for reuse by multiple related child classes.'

See tutorial: https://www.pythontutorial.net/python-oop/python-mixin/

"""
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from opal.patients.models import Relationship

if TYPE_CHECKING:
    from opal.legacy.models import LegacyAppointment


class UnreadQuerySetMixin(models.Manager):
    """legacy models unread count mixin."""

    def get_unread_queryset(self, patient_sernum: int, user_name: str) -> models.QuerySet:
        """
        Get the queryset of unread model records for a given user.

        Args:
            patient_sernum: User sernum used to retrieve unread model records queryset.
            user_name: Firebase username making the request.

        Returns:
            Queryset of unread model records.
        """
        return self.filter(patientsernum=patient_sernum).exclude(readby__contains=user_name)

    def get_unread_multiple_patients_queryset(self, user_name: str) -> models.QuerySet:
        """
        Get the queryset of unread model records for all patient related to the requestion user.

        Args:
            user_name: Firebase username making the request.

        Returns:
            Queryset of unread model records.
        """
        patient_ids = Relationship.objects.get_patient_id_list_for_caregiver(user_name)
        return self.filter(patientsernum__in=patient_ids).exclude(readby__contains=user_name)


class LegacyNotificationManager(UnreadQuerySetMixin, models.Manager):
    """legacy notification manager."""


class LegacyAppointmentManager(models.Manager):
    """legacy appointment manager."""

    def get_unread_queryset(self, patient_sernum: int, user_name: str) -> models.QuerySet:
        """
        Get the queryset of uncompleted appointments for a given user.

        Args:
            patient_sernum: User sernum used to retrieve uncompleted appointments queryset.
            user_name: Firebase username making the request.

        Returns:
            Queryset of uncompleted appointments.
        """
        return self.filter(
            patientsernum=patient_sernum,
            state='Active',
        ).exclude(
            readby__contains=user_name,
        )

    def get_daily_appointments(self, user_name: str) -> models.QuerySet['LegacyAppointment']:
        """
        Get all appointment for the current day for caregiver related patient(s).

        Used by the home page of the app for checkin.

        Args:
            user_name: Firebase username making the request.

        Returns:
            Appointments schedule for the current day.
        """
        patient_ids = Relationship.objects.get_patient_id_list_for_caregiver(user_name)
        return self.select_related(
            'aliasexpressionsernum',
            'aliasexpressionsernum__aliassernum',
            'aliasexpressionsernum__aliassernum__appointmentcheckin',
        ).filter(
            scheduledstarttime__date=timezone.localtime(timezone.now()).date(),
            patientsernum__in=patient_ids,
            state='Active',
        ).exclude(
            status='Deleted',
        )


class LegacyDocumentManager(UnreadQuerySetMixin, models.Manager):
    """legacy document manager."""


class LegacyTxTeamMessageManager(UnreadQuerySetMixin, models.Manager):
    """legacy txteammessage manager."""


class LegacyEducationalMaterialManager(UnreadQuerySetMixin, models.Manager):
    """legacy educational material manager."""


class LegacyQuestionnaireManager(models.Manager):
    """legacy questionnaire manager."""

    def get_unread_queryset(self, patient_sernum: int) -> models.QuerySet:
        """
        Get the queryset of uncompleted questionnaires for a given user.

        Args:
            patient_sernum: User sernum used to retrieve uncompleted questionnaires queryset.

        Returns:
            Queryset of uncompleted questionnaires.
        """
        return self.filter(patientsernum=patient_sernum, completedflag=0)


class LegacyAnnouncementManager(models.Manager):
    """legacy announcement manager."""

    def get_unread_queryset(self, patient_sernum_list: list[int]) -> int:
        """
        Get the count of unread announcement(s) for a given user and their relationship(s).

        Args:
            patient_sernum_list: List of legacy patient sernum to fetch the annoucements for.

        Returns:
            Count of unread annoucement(s) records.
        """
        return self.filter(
            patientsernum__in=patient_sernum_list,
            readstatus=0,
        ).values(
            'postcontrolsernum',
        ).distinct().count() or 0
