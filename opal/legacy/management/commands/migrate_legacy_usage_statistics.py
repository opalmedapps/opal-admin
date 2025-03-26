"""Management command for migrate legacy usage statistics to new backend usage statistics system."""
from datetime import datetime
from typing import Any, Tuple, Union

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils import timezone

from opal.patients.models import Patient, Relationship
from opal.usage_statistics.models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity

LEGACY_ACTIVITY_LOG_QUERY = """
    SELECT
        PatientSerNum,
        Last_Login,
        Count_Login,
        Count_Checkin,
        Count_Clinical_Notes,
        Count_Educational_Material,
        Count_Feedback,
        Count_Questionnaire,
        Count_LabResults,
        Count_Update_Security_Answer,
        Count_Update_Password,
        Date_Added
    FROM rpt_patient_activity_log;
"""

LEGACY_DATA_RECEIVED_LOG_QUERY = """
    SELECT
        rpl.PatientSerNum,
        rpl.Next_Appointment,
        rpl.Last_Appointment_Received,
        rpl.Last_Clinical_Notes_Received,
        rpl.Last_Lab_Received,
        rpll.Count_Labs,
        rpl.Date_Added
    FROM rpt_patient_labs_log rpll
    INNER JOIN rpt_patient_log rpl
    ON rpll.PatientSerNum = rpl.PatientSerNum;
"""


class Command(BaseCommand):
    """Command to migrate legacy usage statistics from legacy report into new backend system."""

    help = 'Migrate legacy usage statistics from OpalRPT'  # noqa: A003

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migration of the legacy usage statistics.

        Return 'None'.

        Args:
            args: Input arguments.
            kwargs: Input keyword arguments.
        """
        with connections['report'].cursor() as report_db:
            report_db.execute(LEGACY_ACTIVITY_LOG_QUERY)
            self.legacy_activity_logs = report_db.fetchall()
            report_db.execute(LEGACY_DATA_RECEIVED_LOG_QUERY)
            self.legacy_data_received_logs = report_db.fetchall()

        legacy_activity_log_count = 0
        for activity_log in self.legacy_activity_logs:
            try:
                self._migrate_legacy_patient_activity_log(activity_log)
            except Exception as la_exc:
                self.stderr.write(
                    (
                        'Cannot import patient legacy activity log for patient (legacy ID: {patient_id}),'
                        + ' detail: {detail}.'
                    ).format(
                        patient_id=activity_log[0],
                        detail=la_exc,
                    ))
            else:
                legacy_activity_log_count += 1

        self.stdout.write(
            f'Number of imported legacy activity log is: {legacy_activity_log_count}'
            + f'(out of {len(self.legacy_activity_logs)})',
        )
        legacy_data_received_log_count = 0
        for data_received_log in self.legacy_data_received_logs:
            try:
                self._migrate_legacy_patient_data_received_log(data_received_log)
            except Exception as ldr_exc:
                self.stderr.write(
                    (
                        'Cannot import patient legacy data received log for patient (legacy ID: {patient_id}),'
                        + ' detail: {detail}.'
                    ).format(
                        patient_id=data_received_log[0],
                        detail=ldr_exc,
                    ))
            else:
                legacy_data_received_log_count += 1

        self.stdout.write(
            f'Number of imported legacy data received log is: {legacy_data_received_log_count}'
            + f'(out of {len(self.legacy_data_received_logs)})',
        )

    def _migrate_legacy_patient_activity_log(
        self,
        activity_log: Tuple[int, Union[datetime, None], int, int, int, int, int, int, int, int, int, datetime],      # noqa: WPS221 E501
    ) -> None:
        """
        Migrate legacy patient activity log.

        Return 'None'.

        Raises:
            ValueError: If the legacy patient is missing in system

        Args:
            activity_log: legacy patient activity log
        """
        patient = Patient.objects.filter(legacy_id=activity_log[0]).first()
        relationship = Relationship.objects.filter(patient=patient, type=1).first()
        last_login = timezone.make_aware(activity_log[1]) if activity_log[1] else None
        if patient and relationship:
            app_activity = DailyUserAppActivity(
                action_by_user=relationship.caregiver.user,
                last_login=last_login,
                count_logins=activity_log[2],
                count_feedback=activity_log[6],
                count_update_security_answers=activity_log[9],
                count_update_passwords=activity_log[10],
                count_update_language=0,
                count_device_ios=0,
                count_device_android=0,
                count_device_browser=0,
                date_added=activity_log[-1],
            )
            app_activity.full_clean()

            patient_activity = DailyUserPatientActivity(
                action_by_user=relationship.caregiver.user,
                user_relationship_to_patient=relationship,
                patient=patient,
                count_checkins=activity_log[3],
                count_documents=activity_log[4],
                count_educational_materials=activity_log[5],
                count_questionnaires_complete=activity_log[7],
                count_labs=activity_log[8],
            )
            patient_activity.full_clean()

            app_activity.save()
            patient_activity.save()
        else:
            raise ValueError(f'Patient (legacy ID: {activity_log[0]} not not exist in system.')

    def _migrate_legacy_patient_data_received_log(    # noqa: WPS210
        self,
        data_received_log: tuple[int, Union[datetime, None], Union[datetime, None], Union[datetime, None], Union[datetime, None], int, datetime],    # noqa: WPS221 E501
    ) -> None:
        """
        Migrate legacy patient data received log.

        Return 'None'.

        Raises:
            ValueError: If the legacy patient is missing in system

        Args:
            data_received_log: legacy patient data received log
        """
        patient = Patient.objects.filter(legacy_id=data_received_log[0]).first()
        next_appointment = timezone.make_aware(data_received_log[1]) if data_received_log[1] else None
        last_appointment_received = timezone.make_aware(data_received_log[2]) if data_received_log[2] else None
        last_document_received = timezone.make_aware(data_received_log[3]) if data_received_log[3] else None
        last_lab_received = timezone.make_aware(data_received_log[4]) if data_received_log[4] else None
        if patient:
            migrate_record = DailyPatientDataReceived(
                patient=patient,
                next_appointment=next_appointment,
                last_appointment_received=last_appointment_received,
                appointments_received=0,
                last_document_received=last_document_received,
                documents_received=0,
                last_educational_material_received=None,
                educational_materials_received=0,
                last_questionnaire_received=None,
                questionnaires_received=0,
                last_lab_received=last_lab_received,
                labs_received=data_received_log[5],
                date_added=data_received_log[6],
            )
            migrate_record.full_clean()
            migrate_record.save()
        else:
            raise ValueError(f'Patient (legacy ID: {data_received_log[0]} not not exist in system.')
