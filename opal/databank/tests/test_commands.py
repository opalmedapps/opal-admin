from collections import defaultdict
from datetime import datetime, timedelta
from http import HTTPStatus

from django.core.management.base import CommandError
from django.utils import timezone

import pytest
import requests
from pytest_django.asserts import assertRaisesMessage
from pytest_mock.plugin import MockerFixture

from opal.core.test_utils import CommandTestMixin, RequestMockerTest
from opal.databank import factories as databank_factories
from opal.databank import models as databank_models
from opal.legacy import factories as legacy_factories
from opal.legacy_questionnaires import factories as legacy_questionnaire_factories
from opal.patients import factories as patient_factories

from ..management.commands import send_databank_data

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


class TestSendDatabankDataMigration(CommandTestMixin):
    """Test class for databank data donation."""

    def test_command_initialize_fields(self) -> None:
        """Verify the command fields are created upon initializing command."""
        command = send_databank_data.Command()
        assert isinstance(command.command_called, datetime)
        assert isinstance(command.patient_data_success_tracker, defaultdict)
        assert command.command_called is not None

    def test_no_consenting_patients_found_error(self) -> None:
        """Verify correct errors show in stderr for no patients found."""
        message, error = self._call_command('send_databank_data')
        assert not error
        assert 'No patients found consenting to Appointments data donation.' in message
        assert 'No patients found consenting to Demographics data donation.' in message
        assert 'No patients found consenting to Diagnoses data donation.' in message
        assert 'No patients found consenting to Labs data donation.' in message
        assert 'No patients found consenting to Questionnaires data donation.' in message

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

    def test_retrieve_databank_data_for_patient(self, capsys: pytest.CaptureFixture) -> None:  # noqa: WPS213
        """Test fetching the existing data of patients who have consented."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        legacy_questionnaire_factories.LegacyPatientFactory(external_id=51)
        # Must set the last sync date to before the hardcoded last_updated date in our test_QuestionnaireDB.sql data
        last_sync = datetime(2022, 1, 1)
        databank_patient = databank_factories.DatabankConsent(
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

        command = send_databank_data.Command()
        command._retrieve_databank_data_for_patient(databank_patient, databank_models.DataModuleType.APPOINTMENTS)
        command._retrieve_databank_data_for_patient(databank_patient, databank_models.DataModuleType.DEMOGRAPHICS)
        command._retrieve_databank_data_for_patient(databank_patient, databank_models.DataModuleType.DIAGNOSES)
        command._retrieve_databank_data_for_patient(databank_patient, databank_models.DataModuleType.LABS)
        command._retrieve_databank_data_for_patient(databank_patient, databank_models.DataModuleType.QUESTIONNAIRES)
        captured = capsys.readouterr()

        assert f'2 instances of Appointments found for {django_pat1}' in captured.out
        assert f'1 instances of Diagnoses found for {django_pat1}' in captured.out
        assert f'3 instances of Labs found for {django_pat1}' in captured.out
        assert f'1 instances of Demographics found for {django_pat1}' in captured.out
        assert f'7 instances of Questionnaires found for {django_pat1}' in captured.out
        assert not captured.err

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

    def test_send_to_oie_request_exception(self, mocker: MockerFixture, capsys: pytest.CaptureFixture) -> None:
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
        command = send_databank_data.Command()
        command._send_to_oie_and_handle_response({})
        captured = capsys.readouterr()
        assert 'Databank sender OIE Error: request failed' in captured.err

    def test_demographics_success_response(self, mocker: MockerFixture) -> None:
        """Test the expected response for demographics data sending."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id, first_name='Homer')
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data=self._create_custom_oie_response(databank_models.DataModuleType.DEMOGRAPHICS),
        )
        message, error = self._call_command('send_databank_data')
        assert 'Number of Demographics-consenting patients is: 2' in message
        assert databank_models.SharedData.objects.all().count() == 2
        assert not error

    def test_labs_success_response(self, mocker: MockerFixture) -> None:  # noqa: WPS213
        """Test the expected response for labs data sending."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_pat2 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1)
        databank_patient1 = databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=timezone.make_aware(last_sync),
        )
        databank_patient2 = databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=timezone.make_aware(last_sync),
        )
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat2)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat2)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat2)
        response = RequestMockerTest.mock_requests_post(
            mocker,
            response_data=self._create_custom_oie_response(databank_models.DataModuleType.LABS),
        )
        message, error = self._call_command('send_databank_data')
        assert response.return_value.status_code == HTTPStatus.OK
        assert 'Number of Labs-consenting patients is: 2' in message
        assert f'Databank confirmation of data received for {databank_patient1}: 3 labs inserted' in message
        assert f'Databank confirmation of data received for {databank_patient2}: 3 labs inserted' in message
        assert databank_models.SharedData.objects.all().count() == 6
        assert not error

    def test_unrecognized_module_prefix_in_oie_response(self, mocker: MockerFixture) -> None:
        """Ensure an error is logged when the data type is unrecognized in the response data."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=timezone.make_aware(last_sync),
        )
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data={
                'INVALIDTYPE_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [200, '[]'],
            },
        )
        _, error = self._call_command('send_databank_data')
        assert 'Unrecognized module prefix in response' in error

    def test_last_synchronized_updated_success(self, mocker: MockerFixture) -> None:
        """Ensure the last_synchro time is updated if there were no sender errors."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id, first_name='Homer')
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data=self._create_custom_oie_response(databank_models.DataModuleType.DEMOGRAPHICS),
        )
        command = send_databank_data.Command()
        command.handle()
        assert databank_models.SharedData.objects.all().count() == 2
        for databank_patient in databank_models.DatabankConsent.objects.all():
            assert command.patient_data_success_tracker[databank_patient.guid] == {
                databank_models.DataModuleType.APPOINTMENTS: True,
                databank_models.DataModuleType.DIAGNOSES: True,
                databank_models.DataModuleType.DEMOGRAPHICS: True,
                databank_models.DataModuleType.LABS: True,
                databank_models.DataModuleType.QUESTIONNAIRES: True,
            }
            assert databank_patient.last_synchronized == command.command_called

    def test_last_synchronized_not_updated_failure(self, mocker: MockerFixture) -> None:
        """Ensure the last_synchro time is not updated if there was at least one sender error."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        # Make patient1 a failed response
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data={
                'demo_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [400, '[]'],
                'demo_93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d': [201, '[]'],
            },
        )
        command = send_databank_data.Command()
        command.handle()

        databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        databank_patient2 = databank_models.DatabankConsent.objects.get(
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
        )

        assert databank_models.SharedData.objects.all().count() == 1
        assert databank_patient1.last_synchronized == timezone.make_aware(last_sync)
        assert databank_patient2.last_synchronized == command.command_called

    def test_update_databank_patient_metadata_call(self, mocker: MockerFixture) -> None:
        """Test correct calling of the metatdata update."""
        response_data = self._create_custom_oie_response(databank_models.DataModuleType.DEMOGRAPHICS)
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        original_data_sent = [
            {
                'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.DEMOGRAPHICS: [
                    {'patient_id': 51},
                ],
            },
            {
                'GUID': '93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
                databank_models.DataModuleType.DEMOGRAPHICS: [
                    {'patient_id': 52},
                ],
            },
        ]
        command = send_databank_data.Command()
        mock_update_method = mocker.patch.object(
            command,
            '_update_databank_patient_metadata',
        )
        command._parse_aggregate_databank_response(response_data, original_data_sent=original_data_sent)
        mock_update_method.assert_called()
        assert mock_update_method.call_count == len(response_data)
        call_args = mock_update_method.call_args_list[0]
        databank_patient, synced_data, message = call_args.args
        assert isinstance(databank_patient, databank_models.DatabankConsent)
        assert isinstance(synced_data, dict)
        assert isinstance(message, str)

    def test_empty_synced_patient_data(self, mocker: MockerFixture) -> None:
        """Test structure of synced_patient_data if guid not found in original data."""
        response_data = {
            'demo_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
        }
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=timezone.make_aware(last_sync),
        )
        original_data_sent = [
            {
                'GUID': 'UNKNOWN_GUID',
                databank_models.DataModuleType.DEMOGRAPHICS: [
                    {'patient_id': 51},
                ],
            },
        ]
        command = send_databank_data.Command()
        mock_update_method = mocker.patch.object(
            command,
            '_update_databank_patient_metadata',
        )
        command._parse_aggregate_databank_response(response_data, original_data_sent=original_data_sent)
        mock_update_method.assert_called()
        assert mock_update_method.call_count == len(response_data)
        call_args = mock_update_method.call_args_list[0]
        _, synced_data, _ = call_args.args
        assert not synced_data

    def test_update_metadata_with_labs_data(self) -> None:
        """Test just the metadata update part of the labs data type."""
        sent_lab_data = [
            {
                'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.LABS: [
                    {'components': [{'test_result_id': 123}]},
                    {'components': [{'test_result_id': 124}]},
                ],
            },
        ]
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=timezone.make_aware(last_sync),
        )
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        command = send_databank_data.Command()
        mock_databank_patient = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        command._parse_aggregate_databank_response(
            aggregate_response={
                'labs_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '["2 labs inserted"]'],
            },
            original_data_sent=sent_lab_data,
        )
        # Check if SharedData instance is created for lab data
        shared_data_count = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient,
            data_type=databank_models.DataModuleType.LABS,
        ).count()
        assert shared_data_count == 2

        # Additionally, check if the SharedData instance has the correct test_result_id
        shared_data = databank_models.SharedData.objects.get(
            databank_consent=mock_databank_patient,
            data_type=databank_models.DataModuleType.LABS,
            data_id=123,
        )
        assert shared_data.data_id == 123
        shared_data = databank_models.SharedData.objects.get(
            databank_consent=mock_databank_patient,
            data_type=databank_models.DataModuleType.LABS,
            data_id=124,
        )
        assert shared_data.data_id == 124

    def _create_custom_oie_response(self, module: databank_models.DataModuleType) -> dict[str, list]:
        """Prepare a response message according to module and success/failure.

        Args:
            module databank data type

        Returns:
            dictionary of response data
        """
        if module == databank_models.DataModuleType.LABS:
            response_data = {
                'labs_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '["3 labs inserted"]'],
                'labs_93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d': [201, '["3 labs inserted"]'],
            }
        elif module == databank_models.DataModuleType.DEMOGRAPHICS:
            response_data = {
                'demo_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
                'demo_93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d': [201, '[]'],
            }
        return response_data
