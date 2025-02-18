# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any

from django.utils import timezone

import pytest
import requests
from pytest_django.asserts import assertRaisesMessage
from pytest_mock.plugin import MockerFixture

from opal.core.test_utils import CommandTestMixin, RequestMockerTest
from opal.databank import factories as databank_factories
from opal.databank import models as databank_models
from opal.legacy import factories as legacy_factories
from opal.legacy.models import LegacyPatientTestResult
from opal.legacy_questionnaires import factories as legacy_questionnaire_factories
from opal.patients import factories as patient_factories

from ..management.commands import send_databank_data

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


class TestSendDatabankDataMigration(CommandTestMixin):
    """Test class for databank data donation."""

    def test_command_initialize_fields(self) -> None:
        """Verify the command fields are created upon initializing command."""
        command = send_databank_data.Command()
        assert isinstance(command.called_at, datetime)
        assert isinstance(command.patient_data_success_tracker, dict)
        assert command.called_at is not None

    def test_pass_non_default_timeout(self) -> None:
        """Verify the source system timeout argument is properly parsed."""
        message, error = self._call_command('send_databank_data', '--request-timeout', '90')
        assert 'Sending databank data with 90 seconds timeout for source system response.' in message
        assert not error

    def test_no_consenting_patients_found_message(self) -> None:
        """Verify correct notifications show in stdout for no patients found."""
        message, error = self._call_command('send_databank_data')
        assert not error
        assert 'Sending databank data with 120 seconds timeout for source system response.' in message
        assert 'No patients found consenting to Appointments data donation.' in message
        assert 'No patients found consenting to Demographics data donation.' in message
        assert 'No patients found consenting to Diagnoses data donation.' in message
        assert 'No patients found consenting to Labs data donation.' in message
        assert 'No patients found consenting to Questionnaires data donation.' in message

    def test_consenting_patients_found_message(self) -> None:
        """Verify correct errors show in stderr for no patients found."""
        pat1 = patient_factories.Patient(ramq='SIMM87654321')
        yesterday = timezone.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=yesterday,
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
        yesterday = timezone.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=yesterday,
        )
        message, error = self._call_command('send_databank_data')
        assert f'No Appointments data found for {pat1}' in message
        assert f'No Demographics data found for {pat1}' in message
        assert f'No Diagnoses data found for {pat1}' in message
        assert f'No Labs data found for {pat1}' in message
        assert f'No Questionnaires data found for {pat1}' in message
        assert not error

    def test_retrieve_databank_data_for_patient(
        self,
        capsys: pytest.CaptureFixture[str],
        questionnaire_data: None,
    ) -> None:
        """Test fetching the existing data of patients who have consented."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        legacy_questionnaire_factories.LegacyQuestionnairePatientFactory(external_id=51)
        # Must set the last sync date to before the hardcoded last_updated date in our test_QuestionnaireDB.sql data
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_patient = databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=last_sync,
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
        yesterday = timezone.now() - timedelta(days=1)
        databank_patient = databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=yesterday,
        )

        command = send_databank_data.Command()
        message = 'INVA not a valid databank data type.'
        with assertRaisesMessage(ValueError, message):
            command._retrieve_databank_data_for_patient(databank_patient, 'INVA')  # type: ignore[arg-type]

    def test_legacy_id_missing_from_databank_patient(self) -> None:
        """Ensure a value error is raised if a patient doesn't have their legacy id created."""
        django_pat1 = patient_factories.Patient(legacy_id=None)
        yesterday = timezone.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=yesterday,
        )

        message = 'Legacy ID missing from Databank Patient.'
        with assertRaisesMessage(ValueError, message):
            self._call_command('send_databank_data')

    def test_send_to_source_system_bad_configuration_exception(
        self,
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify the request exception is handled when connection details for the source system are wrong."""
        django_pat1 = patient_factories.Patient()
        yesterday = timezone.now() - timedelta(days=1)
        databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=yesterday,
        )
        generated_data = {
            'status': 'error',
            'data': {
                'message': 'No connection adapters were found for HOST',
            },
        }
        mock_post = RequestMockerTest.mock_requests_post(mocker, generated_data)
        mock_post.side_effect = requests.RequestException('No connection adapters were found for HOST')
        mock_post.return_value.status_code = HTTPStatus.BAD_GATEWAY
        command = send_databank_data.Command()
        command._request_and_handle_response({}, 60)
        captured = capsys.readouterr()
        assert 'Source system connection Error: No connection adapters were found for HOST' in captured.err

    def test_send_to_source_system_bad_gateway_error(
        self,
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify bad gateway error is logged to stderr."""
        django_pat1 = patient_factories.Patient()
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_data_to_send = {
            'patientList': [
                {
                    'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                    'DEMO': [
                        {
                            'last_updated': '2023-12-08 11:18:58-05:00',
                            'patient_id': 51,
                            'opal_registration_date': '2023-10-08 11:18:58-04:00',
                            'patient_sex': 'Female',
                            'patient_dob': '1986-10-01 00:00:00-04:00',
                            'patient_primary_language': 'EN',
                            'patient_death_date': '',
                        },
                    ],
                },
            ],
        }
        response_data = {'message': 'Bad Gateway'}
        mock_post = RequestMockerTest.mock_requests_post(mocker, response_data)
        mock_post.return_value.status_code = HTTPStatus.BAD_GATEWAY
        command = send_databank_data.Command()
        command._request_and_handle_response(databank_data_to_send, 60)
        captured = capsys.readouterr()
        assert '502 source system response error' in captured.err
        assert 'Bad Gateway' in captured.err

    def test_send_to_source_system_missing_endpoint_allowance_error(
        self,
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify resource not found (missing endpoint in nginx) is logged."""
        django_pat1 = patient_factories.Patient()
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_data_to_send = {
            'patientList': [
                {
                    'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                    'DEMO': [
                        {
                            'last_updated': '2023-12-08 11:18:58-05:00',
                            'patient_id': 51,
                            'opal_registration_date': '2023-10-08 11:18:58-04:00',
                            'patient_sex': 'Female',
                            'patient_dob': '1986-10-01 00:00:00-04:00',
                            'patient_primary_language': 'EN',
                            'patient_death_date': '',
                        },
                    ],
                },
            ],
        }
        response_data = {'message': 'Resource not found'}
        mock_post = RequestMockerTest.mock_requests_post(mocker, response_data)
        mock_post.return_value.status_code = HTTPStatus.NOT_FOUND
        command = send_databank_data.Command()
        command._request_and_handle_response(databank_data_to_send, 60)
        captured = capsys.readouterr()
        assert '404 source system response error' in captured.err
        assert 'Resource not found' in captured.err

    def test_demographics_success_response(self, mocker: MockerFixture) -> None:
        """Test the expected response for demographics data sending."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id, first_name='Homer')
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data=self._create_custom_source_system_response(databank_models.DataModuleType.DEMOGRAPHICS),
        )
        message, error = self._call_command('send_databank_data')
        assert 'Number of Demographics-consenting patients is: 2' in message
        assert databank_models.SharedData.objects.all().count() == 2
        assert not error

    def test_labs_success_response(self, mocker: MockerFixture) -> None:
        """Test the expected response for labs data sending."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_pat2 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_patient1 = databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=last_sync,
        )
        databank_patient2 = databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=last_sync,
        )
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat2)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat2)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat2)
        response = RequestMockerTest.mock_requests_post(
            mocker,
            response_data=self._create_custom_source_system_response(databank_models.DataModuleType.LABS),
        )
        message, error = self._call_command('send_databank_data')
        assert response.return_value.status_code == HTTPStatus.OK
        assert 'Number of Labs-consenting patients is: 2' in message
        assert f'Databank confirmation of data received for {databank_patient1}: 3 labs inserted' in message
        assert f'Databank confirmation of data received for {databank_patient2}: 3 labs inserted' in message
        assert databank_models.SharedData.objects.all().count() == 6
        assert not error

    def test_unrecognized_module_prefix_in_source_system_response(self, mocker: MockerFixture) -> None:
        """Ensure an error is logged when the data type is unrecognized in the response data."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=last_sync,
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
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data=self._create_custom_source_system_response(databank_models.DataModuleType.DEMOGRAPHICS),
        )
        command = send_databank_data.Command()
        # Pre-init one patients success tracker to test the pass over works correctly in parse_aggregate_response
        command.patient_data_success_tracker['a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274'] = (
            dict.fromkeys(databank_models.DataModuleType, True)
        )
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
            assert databank_patient.last_synchronized == command.called_at

    def test_last_synchronized_not_updated_failure(self, mocker: MockerFixture) -> None:
        """Ensure the last_synchro time is not updated if there was at least one sender error."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        # Make patient1 a failed response
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data={
                'demo_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [400, '[]'],
            },
        )
        command = send_databank_data.Command()
        command.handle()

        databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        assert command.patient_data_success_tracker[databank_patient1.guid] == {
            databank_models.DataModuleType.APPOINTMENTS: True,
            databank_models.DataModuleType.DIAGNOSES: True,
            databank_models.DataModuleType.DEMOGRAPHICS: False,
            databank_models.DataModuleType.LABS: True,
            databank_models.DataModuleType.QUESTIONNAIRES: True,
        }
        assert not all(command.patient_data_success_tracker[databank_patient1.guid].values())
        assert databank_models.SharedData.objects.all().count() == 0
        assert databank_patient1.last_synchronized == last_sync

    def test_parse_aggregate_response_failure_unauthorized(
        self,
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Ensure method not allowed/unauthorized error is correctly handled and SharedData not updated."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        # Make patient1 a failed response
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data={
                'demo_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [
                    405,
                    '["Method Not Allowed"]',
                ],
            },
        )
        command = send_databank_data.Command()
        command.handle()
        captured = capsys.readouterr()
        err_message = (
            '405 error for patient a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274: '
            + 'Method Not Allowed'
        )
        assert err_message in captured.err
        databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        assert command.patient_data_success_tracker[databank_patient1.guid] == {
            databank_models.DataModuleType.APPOINTMENTS: True,
            databank_models.DataModuleType.DIAGNOSES: True,
            databank_models.DataModuleType.DEMOGRAPHICS: False,
            databank_models.DataModuleType.LABS: True,
            databank_models.DataModuleType.QUESTIONNAIRES: True,
        }
        assert not all(command.patient_data_success_tracker[databank_patient1.guid].values())
        assert databank_models.SharedData.objects.all().count() == 0
        assert databank_patient1.last_synchronized == last_sync

    def test_parse_aggregate_response_failure_bad_request(
        self,
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Ensure bad request databank response error is correctly handled and SharedData not updated."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        # Make patient1 a failed response
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data={
                'demo_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [
                    400,
                    '["Data was missing"]',
                ],
            },
        )
        command = send_databank_data.Command()
        command.handle()
        captured = capsys.readouterr()
        err_message = (
            '400 error for patient a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274: '
            + 'Data was missing'
        )
        assert err_message in captured.err
        databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        assert command.patient_data_success_tracker[databank_patient1.guid] == {
            databank_models.DataModuleType.APPOINTMENTS: True,
            databank_models.DataModuleType.DIAGNOSES: True,
            databank_models.DataModuleType.DEMOGRAPHICS: False,
            databank_models.DataModuleType.LABS: True,
            databank_models.DataModuleType.QUESTIONNAIRES: True,
        }
        assert not all(command.patient_data_success_tracker[databank_patient1.guid].values())
        assert databank_models.SharedData.objects.all().count() == 0
        assert databank_patient1.last_synchronized == last_sync

    def test_patient_data_success_tracker_update_success(self) -> None:
        """Test updating last_syncrho times."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        command = send_databank_data.Command()
        command.patient_data_success_tracker[databank_patient1.guid] = (
            dict.fromkeys(databank_models.DataModuleType, True)
        )

        command._update_patients_last_synchronization()
        databank_patient1.refresh_from_db()
        assert databank_patient1.last_synchronized == command.called_at

    def test_patient_data_success_tracker_update_failure(self) -> None:
        """Test failure results in not updating last_syncrho time."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        command = send_databank_data.Command()
        command.patient_data_success_tracker[databank_patient1.guid] = (
            dict.fromkeys(databank_models.DataModuleType, True)
        )
        # Simulate a partial sender error
        command.patient_data_success_tracker[databank_patient1.guid][databank_models.DataModuleType.DEMOGRAPHICS] = False

        command._update_patients_last_synchronization()
        databank_patient1.refresh_from_db()
        assert databank_patient1.last_synchronized == last_sync

    def test_module_not_in_synced_data(self) -> None:
        """Test behaviour when synced_data contains unknown module."""
        sent_data = [
            {
                'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                'INVA': [
                    {'components': [{'test_result_id': 123}]},
                    {'components': [{'test_result_id': 124}]},
                ],
            },
        ]
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=last_sync,
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
            original_data_sent=sent_data,
        )
        # Check if SharedData instance is created for lab data
        shared_data_count = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient,
            data_type=databank_models.DataModuleType.LABS,
        ).count()
        assert shared_data_count == 0

    def test_update_databank_patient_shared_data_call(self, mocker: MockerFixture) -> None:
        """Test correct calling of the metatdata update."""
        response_data = self._create_custom_source_system_response(databank_models.DataModuleType.DEMOGRAPHICS)
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
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
            '_update_databank_patient_shared_data',
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
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
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
            '_update_databank_patient_shared_data',
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
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=True,
            last_synchronized=last_sync,
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

    def test_update_metadata_with_diagnosis_data(self) -> None:
        """Test just the isolated creation of diagnosis-type SharedData instances."""
        sent_diagnoses_data = [
            {
                'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.DIAGNOSES: [
                    {'diagnosis_id': 1},
                    {'diagnosis_id': 2},
                    {'diagnosis_id': 3},
                ],
            },
            {
                'GUID': 'b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.DIAGNOSES: [
                    {'diagnosis_id': 4},
                ],
            },
        ]
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMM12345677', legacy_id=52)
        legacy_pat2 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=True,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=True,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        legacy_factories.LegacyDiagnosisFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyDiagnosisFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyDiagnosisFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyDiagnosisFactory(patient_ser_num=legacy_pat2)
        command = send_databank_data.Command()
        mock_databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        mock_databank_patient2 = databank_models.DatabankConsent.objects.get(
            guid='b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        command._parse_aggregate_databank_response(
            aggregate_response={
                'diag_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
                'diag_b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
            },
            original_data_sent=sent_diagnoses_data,
        )
        # Check if SharedData instance is created for diagnosis data
        shared_data_count1 = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient1,
            data_type=databank_models.DataModuleType.DIAGNOSES,
        ).count()
        assert shared_data_count1 == 3
        shared_data_count2 = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient2,
            data_type=databank_models.DataModuleType.DIAGNOSES,
        ).count()
        assert shared_data_count2 == 1

    def test_update_metadata_with_appointment_data(self) -> None:
        """Test just the isolated creation of appointment-type SharedData instances."""
        sent_appointments_data = [
            {
                'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.APPOINTMENTS: [
                    {'appointment_id': 1},
                    {'appointment_id': 2},
                    {'appointment_id': 3},
                ],
            },
            {
                'GUID': 'b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.APPOINTMENTS: [
                    {'appointment_id': 4},
                ],
            },
        ]
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMM12345677', legacy_id=52)
        legacy_pat2 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=True,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=True,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        legacy_factories.LegacyAppointmentFactory(patientsernum=legacy_pat1)
        legacy_factories.LegacyAppointmentFactory(patientsernum=legacy_pat1)
        legacy_factories.LegacyAppointmentFactory(patientsernum=legacy_pat1)
        legacy_factories.LegacyAppointmentFactory(patientsernum=legacy_pat2)
        command = send_databank_data.Command()
        mock_databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        mock_databank_patient2 = databank_models.DatabankConsent.objects.get(
            guid='b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        command._parse_aggregate_databank_response(
            aggregate_response={
                'appt_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
                'appt_b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
            },
            original_data_sent=sent_appointments_data,
        )
        # Check if SharedData instance is created for appointments data
        shared_data_count1 = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient1,
            data_type=databank_models.DataModuleType.APPOINTMENTS,
        ).count()
        assert shared_data_count1 == 3
        shared_data_count2 = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient2,
            data_type=databank_models.DataModuleType.APPOINTMENTS,
        ).count()
        assert shared_data_count2 == 1

    def test_update_metadata_with_questionnaires_data(self) -> None:
        """Test just the isolated creation of questionnaire-type SharedData instances."""
        sent_questionnaires_data = [
            {
                'GUID': 'a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.QUESTIONNAIRES: [
                    {'answer_questionnaire_id': 1},
                    {'answer_questionnaire_id': 2},
                    {'answer_questionnaire_id': 3},
                ],
            },
            {
                'GUID': 'b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
                databank_models.DataModuleType.QUESTIONNAIRES: [
                    {'answer_questionnaire_id': 4},
                ],
            },
        ]
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        django_pat2 = patient_factories.Patient(ramq='SIMM12345677', legacy_id=52)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=True,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=False,
            has_questionnaires=True,
            has_labs=False,
            last_synchronized=last_sync,
        )
        command = send_databank_data.Command()
        mock_databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        mock_databank_patient2 = databank_models.DatabankConsent.objects.get(
            guid='b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )
        command._parse_aggregate_databank_response(
            aggregate_response={
                'qstn_a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
                'qstn_b12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274': [201, '[]'],
            },
            original_data_sent=sent_questionnaires_data,
        )
        # Check if SharedData instance is created for questionnaires data
        shared_data_count1 = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient1,
            data_type=databank_models.DataModuleType.QUESTIONNAIRES,
        ).count()
        assert shared_data_count1 == 3
        shared_data_count2 = databank_models.SharedData.objects.filter(
            databank_consent=mock_databank_patient2,
            data_type=databank_models.DataModuleType.QUESTIONNAIRES,
        ).count()
        assert shared_data_count2 == 1

    def test_empty_source_system_response(self, mocker: MockerFixture, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that execution doesnt fail if source system response is empty."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        django_pat2 = patient_factories.Patient(ramq='SIMH12345678', legacy_id=52)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat2.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_factories.DatabankConsent(
            patient=django_pat2,
            guid='93265ef54c8026a70a9e385b0ada9f30b5daaa06eb39d2ec0d4e092255f9380d',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        RequestMockerTest.mock_requests_post(
            mocker,
            response_data={},
        )
        command = send_databank_data.Command()
        command.handle()
        captured = capsys.readouterr()
        assert not captured.err

    def test_update_databank_patient_shared_data_partial_sender_error(self) -> None:
        """Test behaviour when the update metadata function is called with partially failed patient data."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        last_sync = datetime(2022, 1, 1, tzinfo=timezone.get_current_timezone())
        databank_factories.DatabankConsent(
            patient=django_pat1,
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
            has_appointments=False,
            has_diagnoses=False,
            has_demographics=True,
            has_questionnaires=False,
            has_labs=False,
            last_synchronized=last_sync,
        )
        databank_patient1 = databank_models.DatabankConsent.objects.get(
            guid='a12c171c8cee87343f14eaae2b034b5a0499abe1f61f1a4bd57d51229bce4274',
        )

        command = send_databank_data.Command()
        # Manually intialize the success tracker for this patient
        command.patient_data_success_tracker[databank_patient1.guid] = (
            dict.fromkeys(databank_models.DataModuleType, True)
        )

        # Set a failed module for the patient
        command.patient_data_success_tracker[databank_patient1.guid][databank_models.DataModuleType.DEMOGRAPHICS] = False

        # synced_data would be empty in this hypothetical situation
        command._update_databank_patient_shared_data(databank_patient1, {})
        assert databank_models.SharedData.objects.all().count() == 0
        assert databank_patient1.last_synchronized == last_sync

    def _questionnaire_answer(self, index: int) -> dict[str, Any]:
        """Return a questionnaire answer for the given index."""
        return {
            'answer_questionnaire_id': 190,
            'creation_date': datetime(2024, 5, 5, 13, 17, 42, tzinfo=timezone.get_current_timezone()),
            'questionnaire_id': 12,
            'questionnaire_title': 'Edmonton Symptom Assessment System',
            'question_id': index,
            'question_text': 'Generic question text',
            'question_display_order': 1,
            'question_type_id': 2,
            'question_type_text': 'Slider',
            'question_answer_id': index,
            'last_updated': datetime(2024, 5, 8, 14, 11, 12, tzinfo=timezone.get_current_timezone()),
            'answer_value': str(index),
        }

    def test_nest_and_serialize_queryset_questionnaires(self) -> None:
        """Verify the custom nesting behaviour works as expected for questionnaires."""
        django_pat1 = patient_factories.Patient()
        yesterday = timezone.now() - timedelta(days=1)
        consent_instance = databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=yesterday,
        )
        # Mock the questionnaire queryset object since we dont use a normal pytest test_QuestionnaireDB connection
        queryset = [self._questionnaire_answer(idx) for idx in range(5)]
        command = send_databank_data.Command()
        result = command._nest_and_serialize_queryset(consent_instance.guid, queryset, 'QSTN')

        assert 'GUID' in result
        assert 'QSTN' in result
        assert isinstance(result['QSTN'], list)
        outer_keys = {
            'answer_questionnaire_id',
            'creation_date',
            'questionnaire_id',
            'questionnaire_title',
            'question_answers',
        }
        inner_keys = {
            'question_id',
            'question_text',
            'question_display_order',
            'question_type_id',
            'question_type_text',
            'question_answer_id',
            'last_updated',
            'answer_value',
        }
        for item in result['QSTN']:
            for key in outer_keys:
                assert key in item
            assert isinstance(item['question_answers'], list)
            for answer in item['question_answers']:
                for key2 in inner_keys:
                    assert key2 in answer

    def test_nest_and_serialize_queryset_labs(self) -> None:
        """Verify the custom nesting behaviour works as expected for labs."""
        django_pat1 = patient_factories.Patient()
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        yesterday = timezone.now() - timedelta(days=1)
        consent_instance = databank_factories.DatabankConsent(
            patient=django_pat1,
            has_appointments=True,
            has_diagnoses=True,
            has_demographics=True,
            has_questionnaires=True,
            has_labs=True,
            last_synchronized=yesterday,
        )
        # Create test data
        for _ in range(5):
            legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)

        # Mock the labs queryset
        queryset = LegacyPatientTestResult.objects.get_databank_data_for_patient(
            patient_ser_num=consent_instance.patient.legacy_id,
            last_synchronized=consent_instance.last_synchronized,
        )
        command = send_databank_data.Command()
        result = command._nest_and_serialize_queryset(consent_instance.guid, queryset, 'LABS')

        assert 'GUID' in result
        assert 'LABS' in result
        assert isinstance(result['LABS'], list)
        outer_keys = {
            'test_group_name',
            'test_group_indicator',
            'specimen_collected_date',
            'components',
        }
        inner_keys = {
            'abnormal_flag',
            'last_updated',
            'test_result_id',
            'component_result_date',
            'test_component_sequence',
            'test_component_name',
            'test_value',
            'test_units',
            'max_norm_range',
            'min_norm_range',
            'source_system',
        }
        for item in result['LABS']:
            for key in outer_keys:
                assert key in item
            assert isinstance(item['components'], list)
            for answer in item['components']:
                for key2 in inner_keys:
                    assert key2 in answer

    def _create_custom_source_system_response(self, module: databank_models.DataModuleType) -> dict[str, list[Any]]:
        """
        Prepare a response message according to module and success/failure.

        Args:
            module: databank data type

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
