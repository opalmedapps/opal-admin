from datetime import datetime

from django.db import DatabaseError
from django.utils import timezone

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.legacy.factories import LegacyAliasExpressionFactory, LegacyPatientFactory, LegacySourceDatabaseFactory

from .. import factories
from ..models import LegacyAppointment, LegacyDiagnosis, LegacyDocument, LegacyPatient, LegacyPatientTestResult

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
        'patient_id',
        'opal_registration_date',
        'patient_sex',
        'patient_dob',
        'patient_primary_language',
        'patient_death_date',
        'last_updated',
    }
    assert databank_data[0]['last_updated'] > last_cron_sync_time
    assert databank_data[0]['patient_id'] == consenting_patient.patientsernum
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
    }
    for lab in databank_data:
        assert lab['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(lab.keys()))

    assert databank_data.count() == 3


def test_create_pathology_document_success() -> None:
    """Ensure a new pathology PDF document record inserted successfully to the OpalDB.Document table."""
    legacy_patient = LegacyPatientFactory()

    LegacySourceDatabaseFactory(source_database_name='OACIS')

    LegacyAliasExpressionFactory(
        expression_name='Pathology',
        description='Pathology',
    )

    LegacyDocument.objects.create_pathology_document(
        legacy_patient_id=legacy_patient.patientsernum,
        prepared_by=1,  # TODO: add LegacyStaff model;
        received_at=timezone.now(),
        report_file_name='test-pathology-pdf-name',
    )

    assert LegacyDocument.objects.count() == 1


def test_create_pathology_document_raises_exception() -> None:
    """Ensure that create_pathology_document method raises exception in case of unsuccessful insertion."""
    legacy_patient = LegacyPatientFactory()

    with assertRaisesMessage(
        DatabaseError,
        'Failed to insert a new pathology PDF document record to the OpalDB.Document table:',
    ):
        LegacyDocument.objects.create_pathology_document(
            legacy_patient_id=legacy_patient.patientsernum,
            prepared_by=1,  # TODO: add LegacyStaff model;
            received_at=timezone.now(),
            report_file_name='test-pathology-pdf-name',
        )

    assert LegacyDocument.objects.count() == 0
