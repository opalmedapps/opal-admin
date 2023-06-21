"""
Module providing legacy model managers to provide the interface through which Legacy DB query operations.

Each manager in this module should be prefixed with `Legacy`

Module also provide mixin classes to make the code reusable.

'A mixin is a class that provides method implementations for reuse by multiple related child classes.'

See tutorial: https://www.pythontutorial.net/python-oop/python-mixin/

"""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, TypeVar

from django.db import models
from django.utils import timezone

from opal.patients.models import Relationship, RelationshipStatus

if TYPE_CHECKING:
    # old version of pyflakes incorrectly detects these as unused
    # can currently not upgrade due to version requirement from wemake-python-styleguide
    from opal.legacy.models import (  # noqa: F401
        LegacyAnnouncement,
        LegacyAppointment,
        LegacyDocument,
        LegacyEducationalMaterial,
        LegacyNotification,
        LegacyQuestionnaire,
        LegacyTxTeamMessage,
    )

_Model = TypeVar('_Model', bound=models.Model)


class UnreadQuerySetMixin(models.Manager[_Model]):
    """legacy models unread count mixin."""

    def get_unread_queryset(self, patient_sernum: int, user_name: str) -> models.QuerySet[_Model]:
        """
        Get the queryset of unread model records for a given user.

        Args:
            patient_sernum: User sernum used to retrieve unread model records queryset.
            user_name: Firebase username making the request.

        Returns:
            Queryset of unread model records.
        """
        return self.filter(patientsernum=patient_sernum).exclude(readby__contains=user_name)

    def get_unread_multiple_patients_queryset(self, user_name: str) -> models.QuerySet[_Model]:
        """
        Get the queryset of unread model records for all patient related to the requestion user.

        Args:
            user_name: Firebase username making the request.

        Returns:
            Queryset of unread model records.
        """
        patient_ids = Relationship.objects.get_patient_id_list_for_caregiver(user_name)
        return self.filter(patientsernum__in=patient_ids).exclude(readby__contains=user_name)


class LegacyNotificationManager(UnreadQuerySetMixin['LegacyNotification'], models.Manager['LegacyNotification']):
    """legacy notification manager."""


class LegacyAppointmentManager(models.Manager['LegacyAppointment']):
    """legacy appointment manager."""

    def get_unread_queryset(self, patient_sernum: int, user_name: str) -> models.QuerySet['LegacyAppointment']:
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
        Get all appointments for the current day for caregiver related patient(s).

        Used by the home page of the app for checkin.

        Args:
            user_name: Firebase username making the request.

        Returns:
            Appointments schedule for the current day.
        """
        relationships = Relationship.objects.get_patient_list_for_caregiver(user_name).filter(
            status=RelationshipStatus.CONFIRMED,
        )
        patient_ids = [
            legacy_id
            for legacy_id in relationships.values_list('patient__legacy_id', flat=True)
            if legacy_id is not None
        ]
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

    def get_closest_appointment(self, user_name: str) -> Optional['LegacyAppointment']:
        """
        Get the closest next appointment in time for any of the patients in the user's care.

        Used by the "Home" page of the app for the "Upcoming Appointment" widget.

        Args:
            user_name: Firebase username making the request

        Returns:
            Closest appointment for the patient in care (including SELF) and their legacy_id
        """
        return self.filter(
            scheduledstarttime__gte=timezone.localtime(timezone.now()),
            patientsernum__in=Relationship.objects.get_patient_id_list_for_caregiver(user_name),
            state='Active',
            status='Open',
        ).order_by(
            'scheduledstarttime',
        ).first()

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
        sent_data_ids: list,
    ) -> models.QuerySet:
        """
        Retrieve the latest de-identified appointment data for a consenting DataBank patient.

        TODO: The sent_data_ids exclusions are theoretically useful to reduce the amount of re-sent data after
        partial sender errors, but by using them we are potentially losing the ability to send data that gets
        updated (under the same data_ser_num) after it has previously been sent to the databank. This is somewhat
        common for labs, for example, so we might not be able to filter out the previously sent ids. TBD

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully
            sent_data_ids: List of ids that have previously been successfully sent to the databank

        Returns:
            Appointment data

        """
        return self.select_related(
            'aliasexpressionsernum',
            'aliasexpressionsernum__aliassernum',
            'source_database',
            'patientsernum',
        ).filter(
            checkin=1,
            patientsernum__patientsernum=patient_ser_num,
            last_updated__gt=last_synchronized,
        ).exclude(
            appointmentsernum__in=sent_data_ids,
        ).annotate(
            appointment_ser_num=models.F('appointmentsernum'),
            date_created=models.F('date_added'),
            source_db_name=models.F('source_database__source_database_name'),
            source_db_alias_code=models.F('aliasexpressionsernum__expression_name'),
            source_db_alias_description=models.F('aliasexpressionsernum__description'),
            source_db_appointment_id=models.F('appointment_aria_ser'),
            alias_name=models.F('aliasexpressionsernum__aliassernum__aliasname_en'),
            scheduled_start_time=models.F('scheduledstarttime'),
        ).values(
            'appointment_ser_num',
            'date_created',
            'source_db_name',
            'source_db_alias_code',
            'source_db_alias_description',
            'source_db_appointment_id',
            'alias_name',
            'scheduledstarttime',
            'scheduled_end_time',
            'last_updated',
        )


class LegacyDocumentManager(UnreadQuerySetMixin['LegacyDocument'], models.Manager['LegacyDocument']):
    """legacy document manager."""


class LegacyTxTeamMessageManager(UnreadQuerySetMixin['LegacyTxTeamMessage'], models.Manager['LegacyTxTeamMessage']):
    """legacy txteammessage manager."""


class LegacyEducationalMaterialManager(
    UnreadQuerySetMixin['LegacyEducationalMaterial'],
    models.Manager['LegacyEducationalMaterial'],
):
    """legacy educational material manager."""


class LegacyQuestionnaireManager(models.Manager['LegacyQuestionnaire']):
    """legacy questionnaire manager."""


class LegacyAnnouncementManager(models.Manager['LegacyAnnouncement']):
    """legacy announcement manager."""

    def get_unread_queryset(self, patient_sernum_list: list[int], user_name: str) -> int:
        """
        Get the count of unread announcement(s) for a given user and their relationship(s).

        Args:
            patient_sernum_list: List of legacy patient sernum to fetch the annoucements for.
            user_name: Username making the request.

        Returns:
            Count of unread annoucement(s) records.
        """
        return self.filter(
            patientsernum__in=patient_sernum_list,
        ).exclude(
            readby__contains=user_name,
        ).values(
            'postcontrolsernum',
        ).distinct().count() or 0


class LegacyPatientManager(models.Manager):
    """LegacyPatient model manager."""

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> Any:
        """
        Retrieve the latest de-identified demographics data for a consenting DataBank patient.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Demographics data

        """
        return self.filter(
            patientsernum=patient_ser_num,
            last_updated__gt=last_synchronized,
        ).annotate(
            patient_ser_num=models.F('patientsernum'),
            opal_registration_date=models.F('registrationdate'),
            patient_sex=models.F('sex'),
            patient_dob=models.F('dateofbirth'),
            patient_primary_language=models.F('language'),
            patient_death_date=models.F('death_date'),
        ).values(
            'patient_ser_num',
            'opal_registration_date',
            'patient_sex',
            'patient_dob',
            'patient_primary_language',
            'patient_death_date',
            'last_updated',
        )
