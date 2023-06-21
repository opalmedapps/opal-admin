from datetime import datetime

from django.utils import timezone

import pytest

from .. import factories
from ..models import LegacyAppointment, LegacyPatient, LegacyDiagnosis, LegacyTestResult

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
    for appointment in databank_data:
        assert appointment['last_updated'] > last_cron_sync_time

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
    assert databank_data[0]['last_updated'] > last_cron_sync_time
    assert databank_data[0]['patient_ser_num'] == consenting_patient.patientsernum
    assert databank_data.count() == 1


def test_get_diagnosis_databank_data() -> None:
    """Ensure diagnosis data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    last_cron_sync_time = timezone.make_aware(datetime(2023, 1, 1, 0, 0, 5))
    # Prepare diagnosis data
    factories.LegacyDiagnosisFactory(patient_ser_num=consenting_patient)
    factories.LegacyDiagnosisFactory(patient_ser_num=consenting_patient)
    # Fetch the data
    databank_data = LegacyDiagnosis.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    print(databank_data)
    assert 1 == 0
    assert databank_data[0]['last_updated'] > last_cron_sync_time
    assert databank_data[0]['patient_ser_num'] == consenting_patient.patientsernum
    assert databank_data.count() == 1


def test_get_labs_databank_data() -> None:
    """Ensure labs data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    last_cron_sync_time = timezone.make_aware(datetime(2023, 1, 1, 0, 0, 5))
    # Prepare labs data
    factories.LegacyTestResultFactory(patient_ser_num=consenting_patient)
    factories.LegacyTestResultFactory(patient_ser_num=consenting_patient)
    # Fetch the data
    databank_data = LegacyTestResult.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    print(databank_data)
    assert 1 == 0
