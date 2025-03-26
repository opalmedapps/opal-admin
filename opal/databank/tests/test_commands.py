from datetime import datetime, timedelta
from http import HTTPStatus

from django.utils import timezone

import pytest
import requests
from pytest_django.asserts import assertRaisesMessage
from pytest_mock.plugin import MockerFixture

from opal.core.test_utils import CommandTestMixin, RequestMockerTest
from opal.databank import factories as databank_factories
from opal.legacy import factories as legacy_factories
from opal.legacy_questionnaires import factories as legacy_questionnaire_factories
from opal.patients import factories as patient_factories

from ..management.commands import send_databank_data

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


class TestSendDatabankDataMigration(CommandTestMixin):
    """Test class for databank data migration."""

    def test_no_consenting_patients_found_error(self) -> None:
        """Verify correct errors show in stderr for no patients found."""
        pat1 = patient_factories.Patient(ramq='SIMM87654321')
        yesterday = datetime.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=pat1,
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(yesterday),
        )
        message, error = self._call_command('send_databank_data')
        assert not message
        assert 'No patients found consenting to Appointments data donation.' in error
        assert 'No patients found consenting to Demographics data donation.' in error
        assert 'No patients found consenting to Diagnoses data donation.' in error
        assert 'No patients found consenting to Labs data donation.' in error
        assert 'No patients found consenting to Questionnaires data donation.' in error

    def test_consenting_patients_found_message(self) -> None:
        """Verify correct errors show in stderr for no patients found."""
        pat1 = patient_factories.Patient(ramq='SIMM87654321')
        yesterday = datetime.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(yesterday),
        )
        message, error = self._call_command('send_databank_data')
        assert 'Number of Appointments-consenting patients is: 1' in message
        assert 'Number of Demographics-consenting patients is: 1' in message
        assert 'Number of Diagnoses-consenting patients is: 1' in message
        assert 'Number of Labs-consenting patients is: 1' in message
        assert 'Number of Questionnaires-consenting patients is: 1' in message
        assert not error

    def test_no_data_found_for_consenting_patient(self) -> None:
        """Verify correct message shows for no data found for patient."""
        pat1 = patient_factories.Patient(first_name='Bart', last_name='Simpson')
        yesterday = datetime.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(yesterday),
        )
        message, error = self._call_command('send_databank_data')
        assert f'No Appointments data found for {pat1}' in message
        assert f'No Demographics data found for {pat1}' in message
        assert f'No Diagnoses data found for {pat1}' in message
        assert f'No Labs data found for {pat1}' in message
        assert f'No Questionnaires data found for {pat1}' in message
        assert not error

    def test_data_found_for_consenting_patient(self, mocker: MockerFixture) -> None:  # noqa: WPS213
        """Test fetching the existing data of patients who have consented."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        legacy_questionnaire_factories.LegacyPatientFactory(external_id=51)
        # Must set the last sync date to before the hardcoded last_updated date in our test_QuestionnaireDB.sql data
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(last_sync),
        )
        legacy_factories.LegacyAppointmentFactory(appointmentsernum=1, checkin=1, patientsernum=legacy_pat1)
        legacy_factories.LegacyAppointmentFactory(appointmentsernum=2, checkin=1, patientsernum=legacy_pat1)
        legacy_factories.LegacyDiagnosisFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        RequestMockerTest.mock_requests_post(mocker, {'status': 'success'})

        message, error = self._call_command('send_databank_data')
        assert f'2 instances of Appointments found for {django_pat1}' in message
        assert f'1 instances of Diagnoses found for {django_pat1}' in message
        assert f'3 instances of Labs found for {django_pat1}' in message
        assert f'1 instances of Demographics found for {django_pat1}' in message
        assert f'7 instances of Questionnaires found for {django_pat1}' in message
        assert not error

    def test_invalid_databank_module(self) -> None:
        """Ensure only the approved databank modules can be passed to the command's protected function."""
        django_pat1 = patient_factories.Patient()
        yesterday = datetime.now() - timedelta(days=1)
        databank_patient = databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(yesterday),
        )

        command = send_databank_data.Command()
        message = 'INVA not a valid databank data type.'
        with assertRaisesMessage(ValueError, message):
            command._retrieve_databank_data_for_patient(databank_patient, 'INVA')  # type: ignore[arg-type]

    def test_legacy_id_missing_from_databank_patient(self) -> None:
        """Ensure a value error is raised if a patient doesn't have their legacy id created."""
        django_pat1 = patient_factories.Patient(legacy_id=None)
        yesterday = datetime.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(yesterday),
        )

        message = 'Legacy ID missing from Databank Patient.'
        with assertRaisesMessage(ValueError, message):
            self._call_command('send_databank_data')

    def test_data_found_for_multiple_patient(self, mocker: MockerFixture) -> None:
        """Test fetching the existing data of multiple patients who have consented."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_pat2 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        # Must set the last sync date to before the hardcoded last_updated date in our test_QuestionnaireDB.sql data
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(last_sync),
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(last_sync),
        )
        legacy_factories.LegacyAppointmentFactory(checkin=1, patientsernum=legacy_pat1)
        legacy_factories.LegacyAppointmentFactory(checkin=1, patientsernum=legacy_pat1)
        legacy_factories.LegacyAppointmentFactory(checkin=1, patientsernum=legacy_pat2)
        legacy_factories.LegacyAppointmentFactory(checkin=0, patientsernum=legacy_pat2)
        RequestMockerTest.mock_requests_post(mocker, {'status': 'success'})
        message, error = self._call_command('send_databank_data')
        for module in ('Appointments', 'Diagnoses', 'Demographics', 'Labs', 'Questionnaires'):
            assert f'Number of {module}-consenting patients is: 2' in message

        assert not error

    def test_partial_sender_error_oie(self, mocker: MockerFixture, capsys: pytest.CaptureFixture) -> None:
        """Verify oie sender errors get properly handled."""
        django_pat1 = patient_factories.Patient()
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        yesterday = datetime.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=timezone.make_aware(yesterday),
        )
        generated_data = {
            'status': 'error',
            'data': {
                'message': 'request failed',
            },
        }
        legacy_factories.LegacyAppointmentFactory(checkin=1, patientsernum=legacy_pat1)
        mock_post = RequestMockerTest.mock_requests_post(mocker, generated_data)
        mock_post.side_effect = requests.RequestException('request failed')
        mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST
        command = send_databank_data.Command()
        command._send_to_oie_and_handle_response({})
        captured = capsys.readouterr()
        assert 'OIE Error: request failed' in captured.err

    def test_demographics_data_sent_first(self, mocker: MockerFixture) -> None:
        """Check that demo data is always the first to be sent to ensure candidate exists in external databank."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1)

        databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_labs=True,
            has_questionnaires=True,
            last_synchronized=timezone.make_aware(last_sync),
        )

        # Create fake data for different modules
        legacy_factories.LegacyAppointmentFactory(appointmentsernum=1, patientsernum=legacy_pat1)
        legacy_factories.LegacyDiagnosisFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)

        # Mock the post request to simulate data being sent
        RequestMockerTest.mock_requests_post(mocker, {'status': 'success'})

        message, error = self._call_command('send_databank_data')

        # Split the message into lines for easier parsing
        message_lines = message.split('\n')

        # Find the index of the first line that contains each message type
        demographics_index = next(
            (idx for idx, line in enumerate(message_lines) if 'Demographics found for' in line), -1,
        )
        labs_index = next(
            (idx for idx, line in enumerate(message_lines) if 'Labs found for' in line), -1,
        )
        appointment_index = next(
            (idx for idx, line in enumerate(message_lines) if 'Appointments found for' in line), -1,
        )
        diagnosis_index = next(
            (idx for idx, line in enumerate(message_lines) if 'Diagnoses found for' in line), -1,
        )
        # Check that the Demographics message index is smaller than the indices of other messages
        assert demographics_index != -1
        assert labs_index > demographics_index
        assert appointment_index > demographics_index
        assert diagnosis_index > demographics_index
        assert not error
