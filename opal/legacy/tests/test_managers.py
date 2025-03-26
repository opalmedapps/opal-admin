from datetime import datetime

from django.utils import timezone

import pytest

from .. import factories
from ..models import LegacyAppointment, LegacyPatient

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_get_appointment_databank_data() -> None:
    """Ensure appointment data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    last_cron_sync_time = timezone.make_aware(datetime(2023, 1, 1, 0, 0, 5))
    # Prepare appointment data
    factories.LegacyAppointmentFactory(appointmentsernum=1, checkin=0)
    factories.LegacyAppointmentFactory(appointmentsernum=2, checkin=0)
    factories.LegacyAppointmentFactory(appointmentsernum=3)
    factories.LegacyAppointmentFactory(appointmentsernum=4)
    # Fetch the data
    databank_data = LegacyAppointment.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )
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
