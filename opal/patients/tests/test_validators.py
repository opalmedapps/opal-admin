from datetime import date, datetime

from django.utils import timezone

import pytest

from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData

from .. import factories, validators

CUSTOMIZED_OIE_PATIENT_DATA = OIEPatientData(
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


def test_some_mrns_have_same_site_code() -> None:
    """Test some MRN records have the same site code."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MGH',
                mrn='9999994',
                active=False,
            ),
            OIEMRNData(
                site='RVH',
                mrn='9999993',
                active=True,
            ),
        ],
    )
    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is True


def test_all_mrns_have_same_site_code() -> None:
    """Test all MRN records have the same site code."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(
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
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=False,
            ),
        ],
    )
    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is True


def test_no_mrns_have_same_site_code() -> None:
    """Test No MRN records have the same site code."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(
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
    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is False


def test_patient_validator_not_deceased_oie_patient() -> None:
    """Ensure `is_deceased` returns False when patients are not deceased for OIE patients."""
    oie_patient = CUSTOMIZED_OIE_PATIENT_DATA

    assert validators.is_deceased(oie_patient) is False


def test_patient_validator_is_deceased_oie_patient() -> None:
    """Ensure deceased patients are caught in the validator for oie patients."""
    oie_patient = CUSTOMIZED_OIE_PATIENT_DATA._replace(deceased=True)

    assert validators.is_deceased(oie_patient) is True


@pytest.mark.django_db()
def test_patient_validator_is_deceased_patient_model() -> None:
    """Ensure deceased patients are caught in the validator for patients of `Patient` model."""
    patient = factories.Patient(date_of_death=timezone.now())

    assert validators.is_deceased(patient) is True


@pytest.mark.django_db()
def test_patient_validator_not_deceased_patient_model() -> None:
    """Ensure `is_deceased` returns False when patients are not deceased in `Patient` model."""
    patient = factories.Patient()

    assert validators.is_deceased(patient) is False
