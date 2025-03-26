"""
Module providing legacy model managers to provide the interface through which Legacy DB query operations.

Each manager in this module should be prefixed with `Legacy`

Module also provide mixin classes to make the code reusable.

'A mixin is a class that provides method implementations for reuse by multiple related child classes.'

See tutorial: https://www.pythontutorial.net/python-oop/python-mixin/

"""
import logging
from collections import namedtuple
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, TypeVar

from django.apps import apps
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import DatabaseError, models
from django.utils import timezone

from django_stubs_ext.aliases import ValuesQuerySet

from opal.patients.models import Relationship, RelationshipStatus

if TYPE_CHECKING:
    # old version of pyflakes incorrectly detects these as unused
    # can currently not upgrade due to version requirement from wemake-python-styleguide
    from opal.legacy.models import (  # noqa: F401, WPS235
        LegacyAnnouncement,
        LegacyAppointment,
        LegacyDiagnosis,
        LegacyDocument,
        LegacyEducationalMaterial,
        LegacyNotification,
        LegacyPatient,
        LegacyPatientActivityLog,
        LegacyPatientControl,
        LegacyPatientTestResult,
        LegacyQuestionnaire,
        LegacyTxTeamMessage,
    )

_Model = TypeVar('_Model', bound=models.Model)

logger = logging.getLogger(__name__)

ReceivedDataLegacyModels = namedtuple(
    'ReceivedDataLegacyModels',
    [
        'LegacyAppointment',
        'LegacyDocument',
        'LegacyEducationalMaterial',
        'LegacyQuestionnaire',
        'LegacyPatientTestResult',
    ],
)


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
        Get the queryset of uncompleted appointments for a given user.

        Args:
            patient_sernum: User sernum used to retrieve uncompleted appointments queryset.
            username: Firebase username making the request.

        Returns:
            Queryset of uncompleted appointments.
        """
        return self.filter(
            patientsernum=patient_sernum,
            state='Active',
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
        return self.filter(
            scheduledstarttime__gte=timezone.localtime(timezone.now()),
            patientsernum__in=patient_ids,
            state='Active',
            status='Open',
        ).order_by(
            'scheduledstarttime',
        ).first()

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> ValuesQuerySet['LegacyAppointment', dict[str, Any]]:
        """
        Retrieve the latest de-identified appointment data for a consenting DataBank patient.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Appointment data

        """
        return self.select_related(
            'aliasexpressionsernum__aliassernum',
            'source_database',
            'patientsernum',
        ).filter(
            checkin=1,
            patientsernum__patientsernum=patient_ser_num,
            last_updated__gt=last_synchronized,
        ).annotate(
            appointment_id=models.F('appointmentsernum'),
            date_created=models.F('date_added'),
            source_db_name=models.F('source_database__source_database_name'),
            source_db_alias_code=models.F('aliasexpressionsernum__expression_name'),
            source_db_alias_description=models.F('aliasexpressionsernum__description'),
            source_db_appointment_id=models.F('appointment_aria_ser'),
            alias_name=models.F('aliasexpressionsernum__aliassernum__aliasname_en'),
            scheduled_start_time=models.F('scheduledstarttime'),
        ).values(
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


class LegacyDocumentManager(UnreadQuerySetMixin['LegacyDocument'], models.Manager['LegacyDocument']):
    """LegacyDocument manager."""

    def create_pathology_document(
        self,
        legacy_patient_id: Optional[int],
        prepared_by: int,
        received_at: datetime,
        report_file_name: str,
    ) -> 'LegacyDocument':
        """Insert a new pathology PDF document record to the OpalDB.Document table.

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
        LegacySourceDatabaseModel = apps.get_model('legacy', 'LegacySourceDatabase')    # noqa: N806

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
            err = 'Failed to insert a new pathology PDF document record to the OpalDB.Document table: {0}'.format(
                exp,
            )
            logger.error(err)
            raise DatabaseError(err)

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
        return self.exclude(
            readby__contains=username,
        ).filter(
            patientsernum__in=patient_sernum_list,
        ).count()


class LegacyPatientManager(models.Manager['LegacyPatient']):
    """LegacyPatient model manager."""

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> ValuesQuerySet['LegacyPatient', dict[str, Any]]:
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
            patient_id=models.F('patientsernum'),
            opal_registration_date=models.F('registration_date'),
            patient_sex=models.F('sex'),
            patient_dob=models.F('date_of_birth'),
            patient_primary_language=models.F('language'),
            patient_death_date=models.F('death_date'),
        ).values(
            'patient_id',
            'opal_registration_date',
            'patient_sex',
            'patient_dob',
            'patient_primary_language',
            'patient_death_date',
            'last_updated',
        )


class LegacyPatientControlManager(models.Manager['LegacyPatientControl']):
    """LegacyPatientControl model manager."""

    def get_aggregated_patient_received_data(
        self,
        start_datetime_period: datetime,
        end_datetime_period: datetime,
    ) -> ValuesQuerySet['LegacyPatientControl', dict[str, Any]]:
        """Retrieve aggregated patients' received data statistics for a given time period.

        The statistics are fetched from the legacy `OpalDB` tables.

        NOTE: The legacy datetime fields are stored in the EST time zone format
        (e.g., zoneinfo.ZoneInfo(key=EST5EDT))), while managed Django models store datetimes in the
        UTC format. Both are time zone aware.

        Args:
            start_datetime_period: the beginning of the time period of app activities being extracted
            end_datetime_period: the end of the time period of app activities being extracted

        Returns:
            Annotated `LegacyPatient` records
        """
        # Perform lazy import by using the `django.apps` to avoid circular imports issue
        legacy_models = ReceivedDataLegacyModels(
            apps.get_model('legacy', 'LegacyAppointment'),
            apps.get_model('legacy', 'LegacyDocument'),
            apps.get_model('legacy', 'LegacyEducationalMaterial'),
            apps.get_model('legacy', 'LegacyQuestionnaire'),
            apps.get_model('legacy', 'LegacyPatientTestResult'),
        )
        patient_out_ref = models.OuterRef('patient')
        date_added_range = (start_datetime_period, end_datetime_period)
        zero_count = models.Value(0)

        annotation_subqueries = {
            # Subqueries for Appointments
            # The appointment statistics are typically for answering questions like:
            #   - How are active the patients in the appointments category?
            #   - How many patients had appointments in the last day, week, month, etc.?"
            'last_appointment_received': models.Subquery(
                # Retrieve the most recent appointment for every patient relatively to the requesting date range,
                # regardless of how old it might be (e.g., the appointment might be older than the start of the range).
                legacy_models.LegacyAppointment.objects.filter(
                    patientsernum=patient_out_ref,
                    scheduledstarttime__lt=end_datetime_period,
                ).order_by('-scheduledstarttime').values('scheduledstarttime')[:1],
            ),

            'next_appointment': models.Subquery(
                # Retrieve the closest open/active appointment for every patient relatively to the requesting
                # date range, regardless of how far it might be.
                # E.g., the appointment might be later than the end of the range.
                legacy_models.LegacyAppointment.objects.filter(
                    patientsernum=patient_out_ref,
                    state='Active',
                    status='Open',
                    scheduledstarttime__gt=end_datetime_period,
                ).order_by('scheduledstarttime').values('scheduledstarttime')[:1],
            ),

            'appointments_received': models.functions.Coalesce(
                # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
                models.Subquery(
                    # Aggregate how many appointments for every patient were received in the given date range.
                    legacy_models.LegacyAppointment.objects.filter(
                        patientsernum=patient_out_ref,
                        date_added__range=date_added_range,
                    ).values(
                        'patientsernum',
                    ).annotate(
                        count=models.Count('appointmentsernum'),
                    ).values('count'),
                ),
                zero_count,
            ),

            # Subqueries for Documents
            'last_document_received': models.Subquery(
                # Retrieve the latest received document for every patient, regardless of how old it might be.
                legacy_models.LegacyDocument.objects.filter(
                    patientsernum=patient_out_ref,
                    dateadded__lt=end_datetime_period,
                ).order_by('-dateadded').values('dateadded')[:1],
            ),

            'documents_received': models.functions.Coalesce(
                # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
                models.Subquery(
                    # Aggregate how many documents for every patient were received in the given date range.
                    legacy_models.LegacyDocument.objects.filter(
                        patientsernum=patient_out_ref,
                        dateadded__range=date_added_range,
                    ).values(
                        'patientsernum',
                    ).annotate(
                        count=models.Count('documentsernum'),
                    ).values('count'),
                ),
                zero_count,
            ),

            # Subqueries for Educational Materials
            'last_educational_material_received': models.Subquery(
                # Retrieve the latest received educational material for every patient,
                # regardless of how old it might be.
                legacy_models.LegacyEducationalMaterial.objects.filter(
                    patientsernum=patient_out_ref,
                    date_added__lt=end_datetime_period,
                ).order_by('-date_added').values('date_added')[:1],
            ),

            'educational_materials_received': models.functions.Coalesce(
                # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
                models.Subquery(
                    # Aggregate how many educational materials for every patient were received in the given date range.
                    legacy_models.LegacyEducationalMaterial.objects.filter(
                        patientsernum=patient_out_ref,
                        date_added__range=date_added_range,
                    ).values(
                        'patientsernum',
                    ).annotate(
                        count=models.Count('educationalmaterialsernum'),
                    ).values('count'),
                ),
                zero_count,
            ),

            # Subqueries for Questionnaires
            'last_questionnaire_received': models.Subquery(
                # Retrieve the latest received questionnaire for every patient, regardless of how old it might be.
                legacy_models.LegacyQuestionnaire.objects.filter(
                    patientsernum=patient_out_ref,
                    date_added__lt=end_datetime_period,
                ).order_by('-date_added').values('date_added')[:1],
            ),

            'questionnaires_received': models.functions.Coalesce(
                # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
                models.Subquery(
                    # Aggregate how many questionnaires for every patient were received in the given date range.
                    legacy_models.LegacyQuestionnaire.objects.filter(
                        patientsernum=patient_out_ref,
                        date_added__range=date_added_range,
                    ).values(
                        'patientsernum',
                    ).annotate(
                        count=models.Count('questionnairesernum'),
                    ).values('count'),
                ),
                zero_count,
            ),

            # Subqueries for Labs
            'last_lab_received': models.Subquery(
                # Retrieve the latest received lab result for every patient, regardless of how old it might be.
                legacy_models.LegacyPatientTestResult.objects.filter(
                    patient_ser_num=patient_out_ref,
                    date_added__lt=end_datetime_period,
                ).order_by('-date_added').values('date_added')[:1],
            ),

            'labs_received': models.functions.Coalesce(
                # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
                models.Subquery(
                    # Aggregate how many lab results for every patient were received in the given date range.
                    legacy_models.LegacyPatientTestResult.objects.filter(
                        patient_ser_num=patient_out_ref,
                        date_added__range=date_added_range,
                    ).values(
                        'patient_ser_num',
                    ).annotate(
                        count=models.Count('patient_test_result_ser_num'),
                    ).values('count'),
                ),
                zero_count,
            ),

            # NOTE! The action_date indicates the date when the patients' data were received.
            # It is not the date when the activity statistics were populated.
            'action_date': models.Value(start_datetime_period.date()),
        }

        return self.annotate(
            **annotation_subqueries,
        ).values(
            'patient',
            *annotation_subqueries,
        )


class LegacyDiagnosisManager(models.Manager['LegacyDiagnosis']):
    """LegacyDiagnosis model manager."""

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> ValuesQuerySet['LegacyDiagnosis', dict[str, Any]]:
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
        For now, we can only return Diagnosis data directly accesible from LegacyDiagnosis.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Diagnosis data
        """
        return self.filter(
            patient_ser_num=patient_ser_num,
            last_updated__gt=last_synchronized,
        ).annotate(
            diagnosis_id=models.F('diagnosis_ser_num'),
            date_created=models.F('creation_date'),
            source_system_code=models.F('diagnosis_code'),
            source_system_code_description=models.F('description_en'),
        ).values(
            'diagnosis_id',
            'date_created',
            'source_system_code',
            'source_system_code_description',
            'last_updated',
        )


class LegacyPatientTestResultManager(models.Manager['LegacyPatientTestResult']):
    """LegacyPatientTestResult model manager."""

    def get_databank_data_for_patient(
        self,
        patient_ser_num: int,
        last_synchronized: datetime,
    ) -> ValuesQuerySet['LegacyPatientTestResult', dict[str, Any]]:
        """
        Retrieve the latest de-identified labs data for a consenting DataBank patient.

        Args:
            patient_ser_num: Legacy OpalDB patient ser num
            last_synchronized: Last time the cron process to send databank data ran successfully

        Returns:
            Lab data
        """
        return self.select_related(
            'test_expression_ser_num',
            'test_group_expression_ser_num',
            'patient_ser_num',
            'test_expression_ser_num__source_database',
        ).filter(
            patient_ser_num=patient_ser_num,
            last_updated__gt=last_synchronized,
        ).annotate(
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
        ).values(
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
        ).order_by('component_result_date', 'test_group_indicator', 'test_component_sequence')

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
    ) -> ValuesQuerySet['LegacyPatientActivityLog', dict[str, Any]]:
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
        return self.filter(
            date_time__gte=start_datetime_period,
            date_time__lt=end_datetime_period,
        ).values(
            'username',
        ).annotate(
            last_login=models.Max('date_time', filter=models.Q(request='Login')),
            count_logins=models.Count('activity_ser_num', filter=models.Q(request='Login')),
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
                'device_id', filter=models.Q(parameters__contains='iOS'), distinct=True,
            ),
            count_device_android=models.Count(
                'device_id', filter=models.Q(parameters__contains='Android'), distinct=True,
            ),
            count_device_browser=models.Count(
                'device_id', filter=models.Q(parameters__contains='browser'), distinct=True,
            ),
        ).filter(
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

    def get_aggregated_patient_app_activities(
        self,
        start_datetime_period: datetime,
        end_datetime_period: datetime,
    ) -> ValuesQuerySet['LegacyPatientActivityLog', dict[str, Any]]:
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
        # TODO: QSCCD-2147. An activity triggered from the Notifications page is recorded differently than
        #       an activity that is initialized in the chart.
        #       E.g., if Marge clicks on a TxTeamMessage notification from her Home page,
        #       the PAL shows Request==GetOneItem, Parameters=={"category":"TxTeamMessages","serNum":"3"}.
        #       Whereas if Marge clicks on a TxTeamMessage from her chart page,
        #       PAL shows Request=Read, Parameters={"Field":"TxTeamMessages","Id":"1"}
        return self.filter(
            date_time__gte=start_datetime_period,
            date_time__lt=end_datetime_period,
        ).exclude(
            target_patient_id=None,
        ).values(
            'target_patient_id',
            'username',
        ).annotate(
            # NOTE: the count includes both successful and failed check-ins
            # TODO: QSCCD-2139. Split the counts of successful from failed check in attempts
            count_checkins=models.Count('activity_ser_num', filter=models.Q(request='Checkin')),
            count_documents=models.Count('activity_ser_num', filter=models.Q(request='DocumentContent')),
            # TODO: QSCCD-2148. Different educational material types get logged differently in PAL table.
            # Package --> Request==Log, Parameters={"Activity":"EducationalMaterialSerNum","ActivityDetails":"6"}
            #  + for each content Request==Log,
            #       and Parameters={"Activity":"EducationalMaterialControlSerNum","ActivityDetails":"649"}
            #         + etc
            # Factsheet --> Request=Log, Parameters={"Activity":"EducationalMaterialSerNum","ActivityDetails":"11"}
            # Booklet --> Log + {"Activity":"EducationalMaterialSerNum","ActivityDetails":"4"}
            #         + for each chapter Request=Read, Parameters={"Field":"EducationalMaterial","Id":"4"}
            # Might have to use PatientActionLog to properly determine educational material count?
            # Could consider counting each type separately here then aggregating below in the model creation?
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
        ).filter(
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
