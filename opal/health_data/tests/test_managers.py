import datetime

from django.utils import timezone

import pytest

from opal.patients import factories as patient_factories

from ..models import QuantitySample, QuantitySampleType, SampleSourceType

pytestmark = pytest.mark.django_db

QUANTITY_SAMPLE_DATA = {  # noqa: WPS407
    'start_date': timezone.now(),
    'device': 'Test Device',
    'source': SampleSourceType.PATIENT,
}


def test_fetch_blood_pressure_measurements_empty_list() -> None:
    """Ensure fetch_blood_pressure_measurements returns empty list with no errors."""
    patient = patient_factories.Patient()
    data = QUANTITY_SAMPLE_DATA.copy()
    QuantitySample.objects.bulk_create([
        QuantitySample(
            **data, patient=patient, type=QuantitySampleType.BODY_MASS, value=60.75,
        ),
        QuantitySample(
            **data, patient=patient, type=QuantitySampleType.BODY_TEMPERATURE, value=36.6,
        ),
    ])
    measurements = QuantitySample.objects.fetch_blood_pressure_measurements(patient)
    assert not measurements


def test_fetch_blood_pressure_measurements_columns_exist() -> None:
    """Ensure fetch_blood_pressure_measurements returns systolic, diastolic, device, and measured_at columns."""
    patient = patient_factories.Patient()
    data = QUANTITY_SAMPLE_DATA.copy()
    QuantitySample.objects.bulk_create([
        QuantitySample(
            **data,
            patient=patient,
            type=QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC,
            value=120,
        ),
        QuantitySample(
            **data,
            patient=patient,
            type=QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC,
            value=80,
        ),
    ])
    measurements = QuantitySample.objects.fetch_blood_pressure_measurements(patient)
    bp_record = measurements[0]

    assert len(measurements) == 1
    assert isinstance(bp_record, dict)
    assert set({'systolic', 'diastolic', 'device', 'measured_at'}).issubset(bp_record.keys())


def test_fetch_blood_pressure_measurements_success() -> None:
    """Ensure fetch_blood_pressure_measurements all the patient's blood pressure records."""
    start_date = timezone.now()

    first_patient = patient_factories.Patient(
        legacy_id=1,
        ramq='SIMM86600111',
    )
    second_patient = patient_factories.Patient(
        legacy_id=2,
        ramq='SIMM86600222',
    )

    data = QUANTITY_SAMPLE_DATA.copy()
    data.pop('start_date')

    QuantitySample.objects.bulk_create([
        QuantitySample(
            **data,
            patient=first_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC,
            value=120,
            start_date=start_date,
        ),
        QuantitySample(
            **data,
            patient=first_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC,
            value=80,
            start_date=start_date,
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BODY_MASS,
            value=60.75,
            start_date=start_date,
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BODY_TEMPERATURE,
            value=36.6,
            start_date=start_date,
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC,
            value=120,
            start_date=start_date,
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC,
            value=80,
            start_date=start_date,
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC,
            value=135,
            start_date=start_date - datetime.timedelta(hours=3),
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC,
            value=90,
            start_date=start_date - datetime.timedelta(hours=3),
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC,
            value=110,
            start_date=start_date - datetime.timedelta(hours=12),
        ),
        QuantitySample(
            **data,
            patient=second_patient,
            type=QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC,
            value=75,
            start_date=start_date - datetime.timedelta(hours=12),
        ),
    ])

    measurements = QuantitySample.objects.fetch_blood_pressure_measurements(second_patient)
    assert len(measurements) == 3
