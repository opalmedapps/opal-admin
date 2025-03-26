from datetime import datetime

from django.utils import timezone

import pytest

from .. import factories
from ..models import LegacyAppointment, LegacyDiagnosis, LegacyPatient, LegacyPatientTestResult

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_get_appointment_databank_data() -> None:
    """Ensure appointment data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    last_cron_sync_time = timezone.make_aware(datetime(2023, 1, 1, 0, 0, 5))
    # Prepare appointment data
    factories.LegacyAppointmentFactory(appointmentsernum=1, checkin=0, patientsernum=consenting_patient)
    factories.LegacyAppointmentFactory(appointmentsernum=2, checkin=0, patientsernum=consenting_patient)
    factories.LegacyAppointmentFactory(appointmentsernum=3, patientsernum=consenting_patient)
    factories.LegacyAppointmentFactory(appointmentsernum=4, patientsernum=consenting_patient)
    # Fetch the data
    databank_data = LegacyAppointment.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'appointment_ser_num',
        'date_created',
        'source_db_name',
        'source_db_alias_code',
        'source_db_alias_description',
        'source_db_appointment_id',
        'alias_name',
        'scheduled_start_time',
        'scheduled_end_time',
        'last_updated',
    }

    for appointment in databank_data:
        assert appointment['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(appointment.keys()))

    assert databank_data.count() == 2


def test_get_demographics_databank_data() -> None:
    """Ensure demographics data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    last_cron_sync_time = timezone.make_aware(datetime(2023, 1, 1, 0, 0, 5))
    # Fetch the data
    databank_data = LegacyPatient.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'patient_ser_num',
        'opal_registration_date',
        'patient_sex',
        'patient_dob',
        'patient_primary_language',
        'patient_death_date',
        'last_updated',
    }
    assert databank_data[0]['last_updated'] > last_cron_sync_time
    assert databank_data[0]['patient_ser_num'] == consenting_patient.patientsernum
    assert databank_data.count() == 1
    assert not (set(expected_returned_fields) - set(databank_data[0].keys()))


def test_get_diagnosis_databank_data() -> None:
    """Ensure diagnosis data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    non_consenting_patient = factories.LegacyPatientFactory(patientsernum=52)
    last_cron_sync_time = timezone.make_aware(datetime(2023, 1, 1, 0, 0, 5))
    # Prepare diagnosis data
    factories.LegacyDiagnosisFactory(patient_ser_num=consenting_patient)
    factories.LegacyDiagnosisFactory(patient_ser_num=consenting_patient)
    factories.LegacyDiagnosisFactory(patient_ser_num=non_consenting_patient)
    # Fetch the data
    databank_data = LegacyDiagnosis.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'diagnosis_id',
        'date_created',
        'source_system',
        'source_system_id',
        'source_system_code',
        'source_system_code_description',
        'stage',
        'stage_criteria',
        'last_updated',
    }
    for diagnosis in databank_data:
        assert diagnosis['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(diagnosis.keys()))

    assert databank_data.count() == 2


def test_get_labs_databank_data() -> None:
    """Ensure labs data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    non_consenting_patient = factories.LegacyPatientFactory(patientsernum=52)
    last_cron_sync_time = timezone.make_aware(datetime(2023, 1, 1, 0, 0, 5))
    # Prepare labs data
    factories.LegacyPatientTestResultFactory(patient_ser_num=consenting_patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=consenting_patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=consenting_patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=non_consenting_patient)
    # Fetch the data
    databank_data = LegacyPatientTestResult.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'test_result_id',
        'collected_date_time',
        'result_date_time',
        'test_group_name',
        'test_component_name',
        'test_value',
        'test_units',
        'max_norm_range',
        'min_norm_range',
        'abnormal_flag',
        'source_system',
        'last_updated',
    }
    for lab in databank_data:
        assert lab['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(lab.keys()))

    assert databank_data.count() == 3
