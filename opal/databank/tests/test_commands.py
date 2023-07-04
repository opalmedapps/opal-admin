from datetime import datetime, timedelta

from django.utils import timezone

import pytest

from opal.core.test_utils import CommandTestMixin
from opal.databank import factories as databank_factories
from opal.legacy import factories as legacy_factories
from opal.legacy_questionnaires import factories as legacy_questionnaire_factories
from opal.patients import factories as patient_factories

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
        assert 'No Appointments data found for Simpson, Bart' in message
        assert 'No Demographics data found for Simpson, Bart' in message
        assert 'No Diagnoses data found for Simpson, Bart' in message
        assert 'No Labs data found for Simpson, Bart' in message
        assert 'No Questionnaires data found for Simpson, Bart' in message
        assert not error

    def test_appointment_data_found_for_consenting_patient(self) -> None:
        """Test fetching the existing appointment data of patients who have consented."""
        django_pat1 = patient_factories.Patient(ramq='SIMM12345678', legacy_id=51)
        legacy_pat1 = legacy_factories.LegacyPatientFactory(patientsernum=django_pat1.legacy_id)
        legacy_questionnaire_factories.LegacyPatientFactory(external_id=51)
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
        legacy_factories.LegacyAppointmentFactory(appointmentsernum=1, checkin=1, patientsernum=legacy_pat1)
        legacy_factories.LegacyAppointmentFactory(appointmentsernum=2, checkin=1, patientsernum=legacy_pat1)
        legacy_factories.LegacyDiagnosisFactory(patient_ser_num=legacy_pat1)
        legacy_factories.LegacyPatientTestResultFactory(patient_ser_num=legacy_pat1)
        message, error = self._call_command('send_databank_data')

        assert '2 instances of Appointments data found, [Temporary print out for test coverage in pipeline]' in message
        assert '1 instances of Diagnoses data found, [Temporary print out for test coverage in pipeline]' in message
        assert '1 instances of Labs data found, [Temporary print out for test coverage in pipeline]' in message
        assert '1 instances of Demographics data found, [Temporary print out for test coverage in pipeline]' in message
        assert not error
