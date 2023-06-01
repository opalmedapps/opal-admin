"""Test module for common validators for `patients` app."""
from datetime import date, datetime

from django.utils import timezone

import pytest

from ...services.hospital.hospital_data import OIEMRNData, OIEPatientData
from .. import factories
from ..validators import has_multiple_mrns_with_same_site_code, is_deceased

pytestmark = pytest.mark.django_db

OIE_PATIENT_DATA = OIEPatientData(
    date_of_birth=date.fromisoformat('1984-05-09'),
    first_name='Marge',
    last_name='Simpson',
    sex='F',
    alias='',
    deceased=False,
    death_date_time=datetime.strptime('2054-05-09 09:20:30', '%Y-%m-%d %H:%M:%S'),
    ramq='MARG99991313',
    ramq_expiration=datetime.strptime('2024-01-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
    mrns=[
        OIEMRNData(
            site='MGH',
            mrn='9999993',
            active=True,
        ),
        OIEMRNData(
            site='MCH',
            mrn='9999994',
            active=True,
        ),
        OIEMRNData(
            site='RVH',
            mrn='9999993',
            active=True,
        ),
    ],
)


def test_patient_validator_is_deceased_oie_patient() -> None:
    """Ensure deceased patients are caught in the validator for oie patients."""
    oie_patient = OIE_PATIENT_DATA._replace(deceased=True)

    assert is_deceased(oie_patient)


def test_patient_validator_is_deceased_patient_model() -> None:
    """Ensure deceased patients are caught in the validator for patients of `Patient` model."""
    patient = factories.Patient(date_of_death=timezone.now())

    assert is_deceased(patient)


def test_patient_validator_has_multiple_mrns_for_one_site() -> None:
    """Ensure multiple mrns for one site are caught in the validator for oie patients."""
    oie_patient = OIE_PATIENT_DATA._replace(
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MGH',
                mrn='9999994',
                active=True,
            ),
        ],
    )

    assert has_multiple_mrns_with_same_site_code(oie_patient)
