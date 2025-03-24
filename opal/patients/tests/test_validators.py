# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import date, datetime

from django.utils import timezone

import pytest

from opal.services.integration.schemas import HospitalNumberSchema, PatientSchema, SexTypeSchema

from .. import factories, validators

CUSTOMIZED_SOURCE_SYSTEM_PATIENT_DATA = PatientSchema(
    first_name='Marge',
    last_name='Simpson',
    date_of_birth=date.fromisoformat('1984-05-09'),
    sex=SexTypeSchema.FEMALE,
    date_of_death=datetime.fromisoformat('2054-05-09 09:20:30'),
    health_insurance_number='MARG99991313',
    mrns=[
        HospitalNumberSchema(
            site='MGH',
            mrn='9999993',
        ),
        HospitalNumberSchema(
            site='MCH',
            mrn='9999994',
        ),
        HospitalNumberSchema(
            site='RVH',
            mrn='9999993',
        ),
    ],
)


def test_some_mrns_have_same_site_code() -> None:
    """Test some MRN records have the same site code."""
    patient_data = PatientSchema.model_copy(CUSTOMIZED_SOURCE_SYSTEM_PATIENT_DATA)
    patient_data.mrns = [
        HospitalNumberSchema(
            site='MGH',
            mrn='9999993',
        ),
        HospitalNumberSchema(
            site='MGH',
            mrn='9999994',
            is_active=False,
        ),
        HospitalNumberSchema(
            site='RVH',
            mrn='9999993',
        ),
    ]

    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is True


def test_all_mrns_have_same_site_code() -> None:
    """Test all MRN records have the same site code."""
    patient_data = PatientSchema.model_copy(CUSTOMIZED_SOURCE_SYSTEM_PATIENT_DATA)
    patient_data.mrns = [
        HospitalNumberSchema(
            site='MGH',
            mrn='9999993',
        ),
        HospitalNumberSchema(
            site='MGH',
            mrn='9999994',
        ),
        HospitalNumberSchema(
            site='MGH',
            mrn='9999993',
            is_active=False,
        ),
    ]

    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is True


def test_no_mrns_have_same_site_code() -> None:
    """Test No MRN records have the same site code."""
    patient_data = PatientSchema.model_copy(CUSTOMIZED_SOURCE_SYSTEM_PATIENT_DATA)
    patient_data.mrns = [
        HospitalNumberSchema(
            site='MGH',
            mrn='9999993',
        ),
        HospitalNumberSchema(
            site='MCH',
            mrn='9999994',
        ),
        HospitalNumberSchema(
            site='RVH',
            mrn='9999993',
        ),
    ]

    assert validators.has_multiple_mrns_with_same_site_code(patient_data) is False


def test_patient_validator_not_deceased_source_system_patient() -> None:
    """Ensure `is_deceased` returns False when patients are not deceased for source system patients."""
    source_system_patient = PatientSchema.model_copy(CUSTOMIZED_SOURCE_SYSTEM_PATIENT_DATA)
    source_system_patient.date_of_death = None

    assert validators.is_deceased(source_system_patient) is False


def test_patient_validator_is_deceased_source_system_patient() -> None:
    """Ensure deceased patients are caught in the validator for source system patients."""
    source_system_patient = CUSTOMIZED_SOURCE_SYSTEM_PATIENT_DATA

    assert validators.is_deceased(source_system_patient) is True


@pytest.mark.django_db
def test_patient_validator_is_deceased_patient_model() -> None:
    """Ensure deceased patients are caught in the validator for patients of `Patient` model."""
    patient = factories.Patient.create(date_of_death=timezone.now())

    assert validators.is_deceased(patient) is True


@pytest.mark.django_db
def test_patient_validator_not_deceased_patient_model() -> None:
    """Ensure `is_deceased` returns False when patients are not deceased in `Patient` model."""
    patient = factories.Patient.create()

    assert validators.is_deceased(patient) is False
