"""Utility functions used by health data app."""
from typing import Final

from django.conf import settings
from django.utils.translation import gettext

import pandas as pd

from opal.patients.models import Patient
from opal.services.charts import ChartData, ChartService

from .models import QuantitySample, QuantitySampleType

BLOOD_PRESSURE_SAMPLE_TYPES: Final = (
    QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC,
    QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC,
)

SINGLE_VALUE_SAMPLE_TYPES: Final = tuple(
    sample for sample in QuantitySampleType if sample not in BLOOD_PRESSURE_SAMPLE_TYPES
)


def build_all_quantity_sample_charts(patient: Patient) -> dict[str, str | None]:
    """Build all the quantity sample charts for a specific patient.

    Args:
        patient: patient for whom charts are being generated

    Returns:
        dictionary of the quantity sample charts in HTML format
    """
    charts: dict[str, str | None] = {}
    chart_service = ChartService()

    # Build charts for the measurements that contain only one value
    for sample_type in SINGLE_VALUE_SAMPLE_TYPES:
        queryset = QuantitySample.objects.order_by('start_date').filter(
            patient=patient,
            type=sample_type,
        ).values('start_date', 'value', 'device')

        df = pd.DataFrame(
            data=list(queryset),
        )

        if df.empty:
            charts[sample_type.label.split(' (')[0]] = None
            continue

        # By default the timezone in the dataframe is UTC.
        # Should be set to the local timezone: https://stackoverflow.com/a/50062101
        df['start_date'] = df['start_date'].dt.tz_convert(settings.TIME_ZONE)

        # Rename start_date, value, device columns to x, y, legend respectively
        df.rename(columns={'start_date': 'x', 'value': 'y', 'device': 'legend'}, inplace=True)

        charts[sample_type.label.split(' (')[0]] = chart_service.generate_line_chart(
            ChartData(
                title=str(sample_type.label),
                label_x=gettext('Date'),
                label_y=str(sample_type.label),
                label_legend=gettext('Device'),
                data=df,
            ),
        )

    # Build charts for the measurements that contain two values (e.g., blood pressure)

    df = pd.DataFrame(QuantitySample.objects.fetch_blood_pressure_measurements(patient))

    if df.empty:
        charts[gettext('Blood Pressure')] = None
    else:
        # By default the timezone in the dataframe is UTC.
        # Should be set to the local timezone: https://stackoverflow.com/a/50062101
        df['measured_at'] = df['measured_at'].dt.tz_convert(settings.TIME_ZONE)

        # Rename start_date, diastolic, systolic, device columns to x, error_max, error_min, legend respectively
        df.rename(
            columns={'measured_at': 'x', 'systolic': 'error_max', 'diastolic': 'error_min', 'device': 'legend'},
            inplace=True,
        )

        charts[gettext('Blood Pressure')] = chart_service.generate_error_bar_chart(
            ChartData(
                title=f"{gettext('Blood Pressure')} (mmHg)",
                label_x=gettext('Date'),
                label_y=gettext('Blood Pressure'),
                label_legend=gettext('Device'),
                data=df,
            ),
            label_error_min=gettext('Diastolic'),
            label_error_max=gettext('Systolic'),
        )

    return charts
