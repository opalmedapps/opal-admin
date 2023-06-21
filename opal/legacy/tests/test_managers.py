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
    # Prepare appointment data and previously sent id list for exclusions
    factories.LegacyAppointmentFactory(appointmentsernum=1, checkin=0)
    factories.LegacyAppointmentFactory(appointmentsernum=2, checkin=0)
    factories.LegacyAppointmentFactory(appointmentsernum=3)
    factories.LegacyAppointmentFactory(appointmentsernum=4)
    factories.LegacyAppointmentFactory(appointmentsernum=5)
    previously_sent_ids = [1, 5]
    # Fetch the data
    databank_data = LegacyAppointment.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
        sent_data_ids=previously_sent_ids,
    )
    for appointment in databank_data:
        assert appointment['last_updated'] > last_cron_sync_time
        assert appointment['appointment_ser_num'] not in previously_sent_ids

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
