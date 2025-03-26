"""Management command for migrating legacy usage statistics to the new backend usage statistics system."""
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandParser
from django.db.models.manager import Manager
from django.utils import timezone

from opal.patients.models import Patient, Relationship, RoleType
from opal.usage_statistics.models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity

NULL_CHARACTER = r'\N'


class Command(BaseCommand):    # noqa: WPS214
    """
    Command to migrate legacy usage statistics from legacy report into new backend system.

    The legacy logs has to be ordered by the patient serial number and the date added.
    eg: python manage.py 'activity_log_file' 'data_received_log_file' --batch-size=1000
    """

    help = 'Migrate legacy usage statistics from OpalRPT'  # noqa: A003

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument('activity_log', type=Path, help='the legacy activity log file path')
        parser.add_argument('data_received_log', type=Path, help='the data received log file path')
        # batch_size is an optional argument with default value of 1000
        parser.add_argument('--batch-size', type=int, help='the migration batch size', default=1000)

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migration of the legacy usage statistics.

        Args:
            args: Input arguments.
            kwargs: Input keyword arguments.
        """
        # query all patients and self relationships

        self.patients = {patient.legacy_id: patient for patient in Patient.objects.all() if patient.legacy_id}
        self.self_caregiver = {
            relationship.patient.legacy_id: relationship
            for relationship in Relationship.objects.filter(type__role_type=RoleType.SELF).all()
            if relationship.patient.legacy_id
        }
        # migrate legacy activity logs
        self.total_legacy_activity_log_count = 0
        legacy_activity_log_count = self._migrate_legacy_patient_activity_logs(
            kwargs['activity_log'],
            kwargs['batch_size'],
        )
        self.stdout.write(
            f'Number of imported legacy activity log is: {legacy_activity_log_count}'
            + f'(out of {self.total_legacy_activity_log_count})',
        )
        # migrate legacy daily data received log
        self.total_legacy_data_received_log_count = 0
        legacy_data_received_log_count = self._migrate_legacy_patient_data_received_logs(
            kwargs['data_received_log'],
            kwargs['batch_size'],
        )
        self.stdout.write(
            f'Number of imported legacy data received log is: {legacy_data_received_log_count}'
            + f'(out of {self.total_legacy_data_received_log_count})',
        )

    def _migrate_legacy_patient_activity_logs(self, file_path: Path, batch_size: int) -> int:    # noqa: WPS231 WPS210 C901 E501
        """
        Migrate list of legacy patient activity logs.

        The legacy patient activity logs should be ordered
        by the patient serial number and the date added.

        Returns the number of record inserted.

        Returns:
            the number of record inserted with success.

        Args:
            file_path: the log file path.
            batch_size: the migration batch size.
        """
        batch_app_activity = []
        batch_patient_activity = []
        last_record = DailyUserPatientActivity.objects.all().last()
        legacy_activity_log_count = 0
        with file_path.open() as data_received_file:
            legacy_activity_logs = csv.DictReader(data_received_file, delimiter=';')
            for row in legacy_activity_logs:
                if (
                    last_record and last_record.patient.legacy_id
                    and last_record.patient.legacy_id >= int(row['PatientSerNum'])
                    and last_record.action_date.strftime('%Y-%m-%d') >= row['Date_Added']
                ):
                    continue
                self.total_legacy_activity_log_count += 1
                try:
                    batch_patient_activity.append(self._create_legacy_patient_activity_log(row))
                except (ValueError, ValidationError) as patient_activity_exc:
                    self.stderr.write(
                        (
                            'Cannot prepare `DailyUserPatientActivity` instance for patient (legacy ID: {patient_id}),'
                            + ' detail: {detail}.'
                        ).format(
                            patient_id=row['PatientSerNum'],
                            detail=patient_activity_exc,
                        ))
                else:
                    if len(batch_patient_activity) == batch_size:
                        self._create_objects_and_clear_batch(    # noqa: WPS220
                            batch_patient_activity,
                            DailyUserPatientActivity.objects,
                        )
                try:
                    batch_app_activity.append(self._create_legacy_app_activity_log(row))
                except (ValueError, ValidationError) as app_activity_exc:
                    self.stderr.write(
                        (
                            'Cannot prepare `DailyUserAppActivity` instance for patient (legacy ID: {patient_id}),'
                            + ' detail: {detail}.'
                        ).format(
                            patient_id=row['PatientSerNum'],
                            detail=app_activity_exc,
                        ))
                else:
                    if len(batch_app_activity) == batch_size:
                        self._create_objects_and_clear_batch(    # noqa: WPS220
                            batch_app_activity,
                            DailyUserAppActivity.objects,
                        )
                    legacy_activity_log_count += 1
        if batch_patient_activity:
            self._create_objects_and_clear_batch(
                batch_patient_activity,
                DailyUserPatientActivity.objects,
            )
        if batch_app_activity:
            self._create_objects_and_clear_batch(
                batch_app_activity,
                DailyUserAppActivity.objects,
            )
        return legacy_activity_log_count

    def _migrate_legacy_patient_data_received_logs(self, file_path: Path, batch_size: int) -> int:    # noqa: WPS210 WPS231 E501
        """
        Migrate list of legacy patient data received logs.

        The legacy patient data received logs should be ordered by
        the patient serial number and the date added.

        Returns:
            the number of record inserted with success.

        Args:
            file_path: the log file path.
            batch_size: the migration batch size.
        """
        batch = []
        last_record = DailyPatientDataReceived.objects.all().last()
        legacy_data_received_log_count = 0
        with file_path.open() as data_received_file:
            legacy_data_received_logs = csv.DictReader(data_received_file, delimiter=';')
            for row in legacy_data_received_logs:
                if (
                    last_record and last_record.patient.legacy_id
                    and last_record.patient.legacy_id >= int(row['PatientSerNum'])
                    and last_record.action_date.strftime('%Y-%m-%d') >= row['Date_Added']
                ):
                    continue
                self.total_legacy_data_received_log_count += 1
                try:
                    batch.append(self._create_legacy_patient_data_received_log(row))
                except (ValueError, ValidationError) as data_received_exc:
                    self.stderr.write(
                        (
                            'Cannot prepare `DailyPatientDataReceived` instance for patient (legacy ID: {patient_id}),'
                            + ' detail: {detail}.'
                        ).format(
                            patient_id=row['PatientSerNum'],
                            detail=data_received_exc,
                        ))
                else:
                    if len(batch) == batch_size:
                        batch = self._create_objects_and_clear_batch(batch, DailyPatientDataReceived.objects)    # noqa: WPS220 E501
                    legacy_data_received_log_count += 1
        # last batch insert
        if batch:
            self._create_objects_and_clear_batch(batch, DailyPatientDataReceived.objects)
        return legacy_data_received_log_count

    def _create_legacy_patient_activity_log(self, activity_log: dict[str, str]) -> DailyUserPatientActivity:
        """
        Create legacy patient activity log.

        Returns:
            DailyUserPatientActivity: activity log object

        Raises:
            ValueError: If the legacy patient is missing in system

        Args:
            activity_log: legacy patient activity log
        """
        legacy_id = int(activity_log['PatientSerNum'])
        if (
            legacy_id in self.patients.keys()
            and legacy_id in self.self_caregiver.keys()
        ):
            patient_activity = DailyUserPatientActivity(
                action_by_user=self.self_caregiver[legacy_id].caregiver.user,
                user_relationship_to_patient=self.self_caregiver[legacy_id],
                patient=self.patients[legacy_id],
                count_checkins=activity_log['Count_Checkin'],
                count_documents=activity_log['Count_Clinical_Notes'],
                count_educational_materials=activity_log['Count_Educational_Material'],
                count_questionnaires_complete=activity_log['Count_Questionnaire'],
                count_labs=activity_log['Count_LabResults'],
                action_date=activity_log['Date_Added'],
            )
            patient_activity.full_clean()
            return patient_activity
        raise ValueError(f'Patient (legacy ID: {legacy_id}) does not exist in system.')

    def _create_legacy_app_activity_log(self, activity_log: dict[str, str]) -> DailyUserAppActivity:
        """
        Create legacy app activity log.

        Returns:
            DailyUserAppActivity: activity log object

        Raises:
            ValueError: If the legacy patient is missing in system

        Args:
            activity_log: legacy patient activity log
        """
        last_login = None if activity_log['Last_Login'] == NULL_CHARACTER else timezone.make_aware(
            datetime.strptime(activity_log['Last_Login'], '%Y-%m-%d %H:%M:%S'),
        )
        legacy_id = int(activity_log['PatientSerNum'])
        if legacy_id in self.self_caregiver.keys():
            app_activity = DailyUserAppActivity(
                action_by_user=self.self_caregiver[legacy_id].caregiver.user,
                last_login=last_login,
                count_logins=activity_log['Count_Login'],
                count_feedback=activity_log['Count_Feedback'],
                count_update_security_answers=activity_log['Count_Update_Security_Answer'],
                count_update_passwords=activity_log['Count_Update_Password'],
                count_update_language=0,
                count_device_ios=0,
                count_device_android=0,
                count_device_browser=0,
                action_date=activity_log['Date_Added'],
            )
            app_activity.full_clean()
            return app_activity
        raise ValueError(f'Patient (legacy ID: {legacy_id}) does not exist in system.')

    def _create_legacy_patient_data_received_log(self, data_received_log: dict[str, str]) -> DailyPatientDataReceived:
        """
        Create legacy patient data received log.

        Returns:
            DailyPatientDataReceived: statistic log object

        Raises:
            ValueError: If the legacy patient is missing in system

        Args:
            data_received_log: legacy patient data received log
        """
        next_appointment = None if data_received_log['Next_Appointment'] == NULL_CHARACTER else timezone.make_aware(
            datetime.strptime(data_received_log['Next_Appointment'], '%Y-%m-%d %H:%M:%S'),
        )
        last_appointment_received = None if data_received_log['Last_Appointment_Received'] == NULL_CHARACTER else timezone.make_aware(    # noqa: E501
            datetime.strptime(data_received_log['Last_Appointment_Received'], '%Y-%m-%d %H:%M:%S'),
        )
        last_document_received = None if data_received_log['Last_Clinical_Notes_Received'] == NULL_CHARACTER else timezone.make_aware(    # noqa: E501
            datetime.strptime(data_received_log['Last_Clinical_Notes_Received'], '%Y-%m-%d %H:%M:%S'),
        )
        last_lab_received = None if data_received_log['Last_Lab_Received'] == NULL_CHARACTER else timezone.make_aware(
            datetime.strptime(data_received_log['Last_Lab_Received'], '%Y-%m-%d %H:%M:%S'),
        )
        if int(data_received_log['PatientSerNum']) in self.patients.keys():
            migrate_record = DailyPatientDataReceived(
                patient=self.patients[int(data_received_log['PatientSerNum'])],
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
                labs_received=data_received_log['Count_Labs'],
                action_date=data_received_log['Date_Added'],
            )
            migrate_record.full_clean()
            return migrate_record
        raise ValueError(f'Patient (legacy ID: {data_received_log["PatientSerNum"]}) does not exist in system.')

    def _create_objects_and_clear_batch(self, batch: list[Any], model: Manager[Any]) -> list[Any]:
        """
        Migrate legacy patient data received log.

        Returns:
            The empty batch size.

        Args:
            batch: List of model object.
            model: Model object created.
        """
        model.bulk_create(batch, batch_size=len(batch))
        batch.clear()
        return batch
