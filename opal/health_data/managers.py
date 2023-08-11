"""Module providing collection of managers and custom querysets for the health_data app."""

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models

from typing_extensions import TypedDict

from . import models as quantity_sample_models

if TYPE_CHECKING:
    from opal.health_data.models import QuantitySample  # noqa: F401
    from opal.patients.models import Patient


BloodPressureMeasurementType = TypedDict(
    'BloodPressureMeasurementType',
    {
        'systolic': Decimal,
        'diastolic': Decimal,
        'measured_at': datetime.datetime,
    },
)


class QuantitySampleManager(models.Manager['QuantitySample']):
    """Manager class for the `QuantitySample` model."""

    def fetch_blood_pressure_measurements(
        self,
        patient: 'Patient',
    ) -> list[dict[str, BloodPressureMeasurementType]]:
        """
        Fetch the blood pressure measurements for a specific patient.

        Each blood pressure record contains systolic and diastolic values, and the time of the measurement.

        Args:
            patient: patient for whom blood pressure measurements are being fetched

        Returns:
            list of dictionaries that contain blood pressure measurements and time when they were captured
        """
        # In the database, systolic and diastolic values are stored as separate measurements (BPS and BPD types).
        # E.g., QuantitySample.objects.filter(patient_id=1).values('start_date', 'value', 'type', 'patient_id') returns
        #
        # `2023-08-01 19:54:23.000000`, `80.00`, `BPS`, `1`
        # `2023-08-01 19:54:23.000000`, `120.00`, `BPD`, `1`
        #
        # The query below merges BPS and BPD measurements by the 'start_date' and returns a list of dictionaries:
        # [{'systolic': '80.00', 'diastolic': '120.00', 'measured_at': 2023-08-01 19:54:23.000000}, ...]

        # Add .order_by() to remove ORDER BY statement that is added by default
        diastolic_measurements = self.filter(
            patient=patient,
            type=quantity_sample_models.QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC,
            start_date=models.OuterRef('start_date'),
            device=models.OuterRef('device'),
            source=models.OuterRef('source'),
        ).order_by().values('value')

        # list() forces QuerySet evaluation that makes call to the database
        return list(
            self.filter(
                patient=patient,
                type=quantity_sample_models.QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC,
            ).annotate(
                systolic=models.F('value'),
                diastolic=diastolic_measurements,
                measured_at=models.F('start_date'),
            ).order_by('measured_at').values('systolic', 'diastolic', 'device', 'measured_at'),
        )
