# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Module providing legacy model managers to provide the interface through which Legacy DB query operations.

Each manager in this module should be prefixed with `Legacy`

Module also provide mixin classes to make the code reusable.

'A mixin is a class that provides method implementations for reuse by multiple related child classes.'

See tutorial: https://www.pythontutorial.net/python-oop/python-mixin/

"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Final, Optional, TypeVar

from django.apps import apps
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import DatabaseError, models
from django.utils import timezone

from opal.patients.models import Relationship, RelationshipStatus

if TYPE_CHECKING:
    # old version of pyflakes incorrectly detects these as unused
    # can currently not upgrade due to version requirement from wemake-python-styleguide
    from opal.legacy.models import (
        LegacyAnnouncement,
        LegacyAppointment,
        LegacyDiagnosis,
        LegacyDocument,
        LegacyEducationalMaterial,
        LegacyNotification,
        LegacyPatient,
        LegacyPatientActivityLog,
        LegacyPatientTestResult,
        LegacyQuestionnaire,
        LegacyTxTeamMessage,
    )

_Model = TypeVar('_Model', bound=models.Model)

logger = logging.getLogger(__name__)

LOGIN_ACTIVITY_FILTER: Final = models.Q(request='Log', parameters__contains='"Activity":"Login"')


class UnreadQuerySetMixin(models.Manager[_Model]):
    """LegacyModels unread count mixin."""

    def get_unread_queryset(self, patient_sernum: int, username: str) -> models.QuerySet[_Model]:
        """
        Get the queryset of unread model records for a given user.

        Args:
            patient_sernum: User sernum used to retrieve unread model records queryset.
            username: Firebase username making the request.

        Returns:
            Queryset of unread model records.
        """
        return self.filter(patientsernum=patient_sernum).exclude(readby__contains=username)

    def get_unread_multiple_patients_queryset(self, username: str) -> models.QuerySet[_Model]:
        """
        Get the queryset of unread model records for all patients related to the requested user.

        Args:
            username: Firebase username making the request.

        Returns:
            Queryset of unread model records.
        """
        patient_ids = Relationship.objects.get_list_of_patients_ids_for_caregiver(
            username=username,
            status=RelationshipStatus.CONFIRMED,
        )
        return self.filter(patientsernum__in=patient_ids).exclude(readby__contains=username)


class LegacyNotificationManager(UnreadQuerySetMixin['LegacyNotification'], models.Manager['LegacyNotification']):
    """LegacyNotification manager."""


class LegacyAppointmentManager(models.Manager['LegacyAppointment']):
    """LegacyAppointment manager."""

    def get_unread_queryset(self, patient_sernum: int, username: str) -> models.QuerySet['LegacyAppointment']:
        """
        Get the queryset of unread appointments for a given user.

        The appointments might contain any statuses and states (e.g., deleted, cancelled, completed, etc.).

        Args:
            patient_sernum: User sernum used to retrieve uncompleted appointments queryset.
            username: Firebase username making the request.

        Returns:
            Queryset of unread appointments with all status/states (e.g., deleted, cancelled, etc.).
        """
        return self.filter(
            patientsernum=patient_sernum,
        ).exclude(
            readby__contains=username,
        )

    def get_daily_appointments(self, username: str) -> models.QuerySet['LegacyAppointment']:
        """
        Get all appointments for the current day for caregiver related patient(s).

        Used by the home page of the app for checkin.

        Args:
            username: Firebase username making the request.

        Returns:
            Appointments schedule for the current day.
        """
        relationships = Relationship.objects.get_patient_list_for_caregiver(username).filter(
            status=RelationshipStatus.CONFIRMED,
        )
        patient_ids = [
            legacy_id
            for legacy_id in relationships.values_list('patient__legacy_id', flat=True)
            if legacy_id is not None
        ]
        return (
            self
            .select_related(
                'aliasexpressionsernum__aliassernum__appointmentcheckin',
                'aliasexpressionsernum__aliassernum__educational_material_control_ser_num',
            )
            .filter(
                scheduledstarttime__date=timezone.localtime(timezone.now()).date(),
                patientsernum__in=patient_ids,
                state='Active',
            )
            .exclude(
                status='Deleted',
            )
        )

    def get_closest_appointment(self, username: str) -> Optional['LegacyAppointment']:
        """
        Get the closest next appointment in time for any of the patients in the user's care.

        Used by the "Home" page of the app for the "Upcoming Appointment" widget.

        Args:
            username: Firebase username making the request

        Returns:
            Closest appointment for the patient in care (including SELF) and their legacy_id
        """
        patient_ids = Relationship.objects.get_list_of_patients_ids_for_caregiver(
            username=username,
            status=RelationshipStatus.CONFIRMED,
        )
        return (
            self
            .filter(
                scheduledstarttime__gte=timezone.localtime(timezone.now()),
                patientsernum__in=patient_ids,
                state='Active',
                status='Open',
            )
            .order_by(
                'scheduledstarttime',
            )
            .first()
        )

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> models.QuerySet['LegacyAppointment', dict[str, Any]]:
        """
        Retrieve the latest de-identified appointment data for a consenting DataBank patient.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Appointment data

        """
        return (
            self
            .select_related(
                'aliasexpressionsernum__aliassernum',
                'source_database',
                'patientsernum',
            )
            .filter(
                checkin=1,
                patientsernum__patientsernum=patient_ser_num,
                last_updated__gt=last_synchronized,
            )
            .annotate(
                appointment_id=models.F('appointmentsernum'),
                date_created=models.F('date_added'),
                source_db_name=models.F('source_database__source_database_name'),
                source_db_alias_code=models.F('aliasexpressionsernum__expression_name'),
                source_db_alias_description=models.F('aliasexpressionsernum__description'),
                source_db_appointment_id=models.F('source_system_id'),
                alias_name=models.F('aliasexpressionsernum__aliassernum__aliasname_en'),
                scheduled_start_time=models.F('scheduledstarttime'),
            )
            .values(
                'appointment_id',
                'date_created',
                'source_db_name',
                'source_db_alias_code',
                'source_db_alias_description',
                'source_db_appointment_id',
                'alias_name',
                'scheduled_start_time',
                'scheduled_end_time',
                'last_updated',
            )
        )


class LegacyDocumentManager(UnreadQuerySetMixin['LegacyDocument'], models.Manager['LegacyDocument']):
    """LegacyDocument manager."""

    def create_pathology_document(
        self,
        legacy_patient_id: int | None,
        prepared_by: int,
        received_at: datetime,
        report_file_name: str,
    ) -> 'LegacyDocument':
        """
        Insert a new pathology PDF document record to the OpalDB.Document table.

        This will indicate that a new pathology report is available for viewing in the app.

        Args:
            legacy_patient_id: legacy patient's ID for whom a new document record being inserted
            prepared_by: `StaffSerNum` from the `OpalDB.LegacyStaff` table that indicates who prepared the report
            received_at: date and time that indicate when the pathology report data were entered into the source system
            report_file_name: filename of the new pathology report document

        Raises:
            DatabaseError: if new `LegacyDocument` instance could not be saved to the database

        Returns:
            newly created and saved `LegacyDocument` instance for the pathology report document
        """
        # Perform lazy import by using the `django.apps` to avoid circular imports issue
        LegacyPatientModel = apps.get_model('legacy', 'LegacyPatient')  # noqa: N806
        LegacyAliasExpressionModel = apps.get_model('legacy', 'LegacyAliasExpression')  # noqa: N806
        LegacySourceDatabaseModel = apps.get_model('legacy', 'LegacySourceDatabase')  # noqa: N806

        try:
            legacy_document = self.create(
                patientsernum=LegacyPatientModel.objects.get(
                    patientsernum=legacy_patient_id,
                ),
                sourcedatabasesernum=LegacySourceDatabaseModel.objects.get(
                    source_database_name='OACIS',
                    enabled=1,
                ),
                aliasexpressionsernum=LegacyAliasExpressionModel.objects.get(
                    expression_name='Pathology',
                    description='Pathology',
                ),
                approvedby=prepared_by,
                approvedtimestamp=received_at,
                authoredbysernum=prepared_by,
                dateofservice=received_at,
                validentry='Y',
                originalfilename=report_file_name,
                finalfilename=report_file_name,
                createdbysernum=prepared_by,
                createdtimestamp=received_at,
                transferstatus='T',
                transferlog='Transfer successful',
                dateadded=timezone.localtime(timezone.now()),
                readstatus=0,
                readby=[],
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned) as exp:
            # raise `DatabaseError` exception if LegacyPatient, LegacyAliasExpression, or LegacySourceDatabase
            # instances cannot be found or multiple instances returned
            err = f'Failed to insert a new pathology PDF document record to the OpalDB.Document table: {exp}'
            logger.exception(err)
            raise DatabaseError(err) from exp

        legacy_document.save()

        return legacy_document


class LegacyTxTeamMessageManager(UnreadQuerySetMixin['LegacyTxTeamMessage'], models.Manager['LegacyTxTeamMessage']):
    """LegacyTxTeamMessage manager."""


class LegacyEducationalMaterialManager(
    UnreadQuerySetMixin['LegacyEducationalMaterial'],
    models.Manager['LegacyEducationalMaterial'],
):
    """LegacyEducationalMaterial manager."""


class LegacyQuestionnaireManager(models.Manager['LegacyQuestionnaire']):
    """LegacyQuestionnaire manager."""


class LegacyAnnouncementManager(models.Manager['LegacyAnnouncement']):
    """LegacyAnnouncement manager."""

    def get_unread_queryset(self, patient_sernum_list: list[int], username: str) -> int:
        """
        Get the count of unread announcement(s) for a given user and their relationship(s).

        Args:
            patient_sernum_list: List of legacy patient sernum to fetch the announcements for.
            username: Username making the request.

        Returns:
            Count of unread announcement(s) records.
        """
        return (
            self
            .exclude(
                readby__contains=username,
            )
            .filter(
                patientsernum__in=patient_sernum_list,
            )
            .count()
        )


class LegacyPatientManager(models.Manager['LegacyPatient']):
    """LegacyPatient model manager."""

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> models.QuerySet['LegacyPatient', dict[str, Any]]:
        """
        Retrieve the latest de-identified demographics data for a consenting DataBank patient.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Demographics data

        """
        return (
            self
            .filter(
                patientsernum=patient_ser_num,
                last_updated__gt=last_synchronized,
            )
            .exclude(
                sex='Unknown',
            )
            .annotate(
                patient_id=models.F('patientsernum'),
                opal_registration_date=models.F('registration_date'),
                patient_sex=models.F('sex'),
                patient_dob=models.F('date_of_birth'),
                patient_primary_language=models.F('language'),
                patient_death_date=models.F('death_date'),
            )
            .values(
                'patient_id',
                'opal_registration_date',
                'patient_sex',
                'patient_dob',
                'patient_primary_language',
                'patient_death_date',
                'last_updated',
            )
        )


class LegacyDiagnosisManager(models.Manager['LegacyDiagnosis']):
    """LegacyDiagnosis model manager."""

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> models.QuerySet['LegacyDiagnosis', dict[str, Any]]:
        """
        Retrieve the latest de-identified diagnosis data for a consenting DataBank patient.

        Due to the pre-existing structure in OpalDB, we unfortunately can't make a join between
        LegacyDiagnosis, LegacyDiagnosisCode, and subsequently LegacyDiagnosisTranslation. The reason
        for this is that Diagnosis and DiagnosisCode do not have a foreign key constraint between them in OpalDB, even
        though that is the only field where a link could exist. Django mandates uniqueness in ForeignKeys so we could
        'ignore' the actual db schema for DiagnosisCode, but in our current test data we actually do have duplicate
        diagnosis codes in both OpalDB.Diagnosis and OpalDB.DiagnosisCode. It's possible to make this join directly
        in MySQL which doesn't throw errors when duplicate keys get returned, but it isn't possible to do in Django ORM.
        Using the `unique_together` trick also won't work because the Legacy models are unmanaged.
        For now, we can only return Diagnosis data directly accessible from LegacyDiagnosis.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Diagnosis data
        """
        return (
            self
            .filter(
                patient_ser_num=patient_ser_num,
                last_updated__gt=last_synchronized,
            )
            .annotate(
                diagnosis_id=models.F('diagnosis_ser_num'),
                date_created=models.F('creation_date'),
                source_system_code=models.F('diagnosis_code'),
                source_system_code_description=models.F('description_en'),
            )
            .values(
                'diagnosis_id',
                'date_created',
                'source_system_code',
                'source_system_code_description',
                'last_updated',
            )
        )


class LegacyPatientTestResultManager(models.Manager['LegacyPatientTestResult']):
    """LegacyPatientTestResult model manager."""

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> models.QuerySet['LegacyPatientTestResult', dict[str, Any]]:
        """
        Retrieve the latest de-identified labs data for a consenting DataBank patient.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Lab data
        """
        return (
            self
            .select_related(
                'test_expression_ser_num',
                'test_group_expression_ser_num',
                'patient_ser_num',
                'test_expression_ser_num__source_database',
            )
            .filter(
                patient_ser_num=patient_ser_num,
                last_updated__gt=last_synchronized,
            )
            .annotate(
                test_result_id=models.F('patient_test_result_ser_num'),
                specimen_collected_date=models.F('collected_date_time'),
                component_result_date=models.F('result_date_time'),
                test_group_name=models.F('test_group_expression_ser_num__expression_name'),
                test_group_indicator=models.F('test_group_expression_ser_num__test_group_expression_ser_num'),
                test_component_sequence=models.F('sequence_num'),
                test_component_name=models.F('test_expression_ser_num__expression_name'),
                test_value=models.F('test_value_numeric'),
                test_units=models.F('unit_description'),
                max_norm_range=models.F('normal_range_max'),
                min_norm_range=models.F('normal_range_min'),
                source_system=models.F('test_expression_ser_num__source_database__source_database_name'),
            )
            .values(
                'test_result_id',
                'specimen_collected_date',
                'component_result_date',
                'test_group_name',
                'test_group_indicator',
                'test_component_sequence',
                'test_component_name',
                'test_value',
                'test_units',
                'max_norm_range',
                'min_norm_range',
                'abnormal_flag',
                'source_system',
                'last_updated',
            )
            .order_by('component_result_date', 'test_group_indicator', 'test_component_sequence')
        )

    def get_unread_queryset(self, patient_sernum: int, username: str) -> models.QuerySet['LegacyPatientTestResult']:
        """
        Get the queryset of unread lab results for a given patient.

        Args:
            patient_sernum: Patient's sernum used to retrieve unread lab results
            username: Firebase username making the request

        Returns:
            Queryset of unread lab results
        """
        return self.filter(
            patient_ser_num=patient_sernum,
            test_expression_ser_num__test_control_ser_num__publish_flag=1,
            available_at__lte=timezone.now(),
        ).exclude(
            read_by__contains=username,
        )


class LegacyPatientActivityLogManager(models.Manager['LegacyPatientActivityLog']):
    """LegacyPatientActivityLog model manager."""

    def get_aggregated_user_app_activities(
        self,
        start_datetime_period: datetime,
        end_datetime_period: datetime,
    ) -> models.QuerySet['LegacyPatientActivityLog', dict[str, Any]]:
        """
        Retrieve aggregated application activity statistics per user for a given time period.

        The statistics are fetched from the legacy `PatientActivityLog` (a.k.a. PAL) table.

        NOTE: The `PatientActivityLog.DateTime` field stores the datetime in the EST time zone format
        (e.g., zoneinfo.ZoneInfo(key=EST5EDT))), while managed Django models store datetimes in the
        UTC format. Both are time zone aware.

        Args:
            start_datetime_period: the beginning of the time period of app activities being extracted
            end_datetime_period: the end of the time period of app activities being extracted

        Returns:
            Annotated `LegacyPatientActivityLog` records
        """
        return (
            self
            .filter(
                date_time__gte=start_datetime_period,
                date_time__lt=end_datetime_period,
            )
            .values(
                'username',
            )
            .annotate(
                last_login=models.Max('date_time', filter=LOGIN_ACTIVITY_FILTER),
                count_logins=models.Count('activity_ser_num', filter=LOGIN_ACTIVITY_FILTER, distinct=True),
                count_feedback=models.Count('activity_ser_num', filter=models.Q(request='Feedback')),
                count_update_security_answers=models.Count(
                    'activity_ser_num',
                    filter=models.Q(request='UpdateSecurityQuestionAnswer'),
                ),
                count_update_passwords=models.Count(
                    'activity_ser_num',
                    filter=models.Q(request='AccountChange', parameters='OMITTED'),
                ),
                count_update_language=models.Count(
                    'activity_ser_num',
                    filter=models.Q(request='AccountChange', parameters__contains='Language'),
                ),
                count_device_ios=models.Count(
                    'activity_ser_num',
                    filter=LOGIN_ACTIVITY_FILTER
                    & models.Q(
                        parameters__contains='"deviceType":"iOS"',
                    ),
                    distinct=True,
                ),
                count_device_android=models.Count(
                    'activity_ser_num',
                    filter=LOGIN_ACTIVITY_FILTER
                    & models.Q(
                        parameters__contains='"deviceType":"Android"',
                    ),
                    distinct=True,
                ),
                count_device_browser=models.Count(
                    'activity_ser_num',
                    filter=LOGIN_ACTIVITY_FILTER
                    & models.Q(
                        parameters__contains='"deviceType":"browser"',
                    ),
                    distinct=True,
                ),
                # NOTE! The action_date indicates the date when the application activities were made.
                # It is not the date when the activity statistics were populated.
                action_date=models.Value(start_datetime_period.date()),
            )
            .filter(
                # Since the query returns each unique pairing of patient+user (e.g., relationship),
                #     we have the potential to have several 'useless' records created here.
                # This might occur if the legacy 'PatientActivityLog' table contains only
                # patient activity records with no user activities.
                #
                # To solve this problem we filter out these rows with 0 counts
                # using a secondary filter to mimic the MySQL `HAVING` clause.
                models.Q(count_logins__gt=0)
                | models.Q(count_feedback__gt=0)
                | models.Q(count_update_security_answers__gt=0)
                | models.Q(count_update_passwords__gt=0)
                | models.Q(count_update_language__gt=0)
                | models.Q(count_device_ios__gt=0)
                | models.Q(count_device_android__gt=0)
                | models.Q(count_device_browser__gt=0),
            )
        )

    def get_aggregated_patient_app_activities(
        self,
        start_datetime_period: datetime,
        end_datetime_period: datetime,
    ) -> models.QuerySet['LegacyPatientActivityLog', dict[str, Any]]:
        """
        Retrieve aggregated application activity statistics per patient for a given time period.

        The statistics are fetched from the legacy `PatientActivityLog` (a.k.a. PAL) table.

        NOTE: The `PatientActivityLog.DateTime` field stores the datetime in the EST time zone format
        (e.g., zoneinfo.ZoneInfo(key=EST5EDT))), while managed Django models store datetimes in the
        UTC format. Both are time zone aware.

        Args:
            start_datetime_period: the beginning of the time period of app activities being extracted
            end_datetime_period: the end of the time period of app activities being extracted

        Returns:
            Annotated `LegacyPatientActivityLog` records
        """
        # NOTE: an activity triggered from the Notifications page is recorded differently than
        #       an activity that is initialized in the chart.
        #       E.g., if Marge clicks on a TxTeamMessage notification from her Home page,
        #       the PAL shows Request==GetOneItem, Parameters=={"category":"TxTeamMessages","serNum":"3"}.
        #       Whereas if Marge clicks on a TxTeamMessage from her chart page,
        #       PAL shows Request=Read, Parameters={"Field":"TxTeamMessages","Id":"1"}
        return (
            self
            .filter(
                date_time__gte=start_datetime_period,
                date_time__lt=end_datetime_period,
            )
            .exclude(
                target_patient_id=None,
            )
            .values(
                'target_patient_id',
                'username',
            )
            .annotate(
                # NOTE: the count includes both successful and failed check-ins
                # TODO: QSCCD-2139. Split the counts of successful from failed check in attempts
                count_checkins=models.Count('activity_ser_num', filter=models.Q(request='Checkin')),
                count_documents=models.Count('activity_ser_num', filter=models.Q(request='DocumentContent')),
                # NOTE: educational materials count does not include opened sub educational materials or chapters.
                # E.g., Package or Booklet educational materials might have sub-materials that won't be counted.
                count_educational_materials=models.Count(
                    'activity_ser_num',
                    filter=models.Q(request='Log', parameters__contains='EducationalMaterialSerNum'),
                ),
                count_questionnaires_complete=models.Count(
                    'activity_ser_num',
                    filter=models.Q(request='QuestionnaireUpdateStatus', parameters__contains='"new_status":"2"'),
                ),
                count_labs=models.Count(
                    'activity_ser_num',
                    filter=models.Q(request='PatientTestTypeResults') | models.Q(request='PatientTestDateResults'),
                ),
                # NOTE! The action_date indicates the date when the application activities were made.
                # It is not the date when the activity statistics were populated.
                action_date=models.Value(start_datetime_period.date()),
            )
            .filter(
                # Since the query returns each unique pairing of patient+user (e.g., relationship),
                #     we have the potential to have several 'useless' records created here.
                # For example, if Fred Flintstone logged in once, did nothing and logged out,
                #     then this query would create one row for Fred's patient activity with all the counts set to 0.
                # Also, a row with with zero counts might be created if user switches the profile to associated profile
                # and makes activities that are not captured by this query (e.g., navigating to the `Notifications` tab).
                #
                # To solve this problem we filter out these rows with 0 counts
                # using a secondary filter to mimic the MySQL `HAVING` clause.
                models.Q(count_checkins__gt=0)
                | models.Q(count_documents__gt=0)
                | models.Q(count_educational_materials__gt=0)
                | models.Q(count_questionnaires_complete__gt=0)
                | models.Q(count_labs__gt=0),
            )
        )
