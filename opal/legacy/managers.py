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

if TYPE_CHECKING:
    from opal.legacy.models import LegacyAppointment


class UnreadQuerySetMixin(models.Manager):
    """legacy models unread count mixin."""

    def get_unread_queryset(self, patient_sernum: int) -> models.QuerySet:
        """
        Get the queryset of unread model records for a given user.

        Args:
            patient_sernum: User sernum used to retrieve unread model records queryset.

        Returns:
            Queryset of unread model records.
        """
        return self.filter(patientsernum=patient_sernum, readstatus=0)


class LegacyNotificationManager(UnreadQuerySetMixin, models.Manager):
    """legacy notification manager."""


class LegacyAppointmentManager(models.Manager):
    """legacy appointment manager."""

    def get_unread_queryset(self, patient_sernum: int) -> models.QuerySet:
        """
        Get the queryset of uncompleted appointments for a given user.

        Args:
            patient_sernum: User sernum used to retrieve uncompleted appointments queryset.

        Returns:
            Queryset of uncompleted appointments.
        """
        return self.filter(
            patientsernum=patient_sernum,
            readstatus=0,
            state='Active',
        ).exclude(
            status='Deleted',
        )

    def get_daily_appointments(self, patient_sernum: int) -> models.QuerySet['LegacyAppointment']:
        """
        Get all appointment for the current day.

        Args:
            patient_sernum: Patient sernum used to retrieve unread notifications count.

        Returns:
            Appointments schedule for the current day.
        """
        return self.select_related(
            'aliasexpressionsernum',
            'aliasexpressionsernum__aliassernum',
            'aliasexpressionsernum__aliassernum__appointmentcheckin',
        ).filter(
            scheduledstarttime__date=timezone.localtime(timezone.now()).date(),
            patientsernum=patient_sernum,
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
        Get the count of unread announcement(s) for a given user and it's relationship(s).

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
