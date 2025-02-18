# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Any

import pytest
from pydantic import ValidationError

from .. import schemas


def test_error_response() -> None:
    """Test the ErrorResponseSchema."""
    response = schemas.ErrorResponseSchema(status_code=404, message='Patient not found')

    assert response.status_code == 404
    assert response.message == 'Patient not found'


def test_hospital_number() -> None:
    """Test the HospitalNumberSchema."""
    hospital_number = schemas.HospitalNumberSchema(mrn='1234', site='TEST')

    assert hospital_number.mrn == '1234'
    assert hospital_number.site == 'TEST'


def test_hospital_number_non_empty() -> None:
    """MRN and site cannot be empty."""
    with pytest.raises(ValidationError) as exc:
        schemas.HospitalNumberSchema(mrn='', site='')

    assert exc.value.error_count() == 2


@pytest.mark.parametrize('sex', schemas.SexType)
def test_patient_minimal(sex: schemas.SexType) -> None:
    """Test the PatientSchema with minimal data."""
    data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': sex.value,
        'date_of_birth': '1986-10-05',
        'date_of_death': None,
        'health_insurance_number': None,
        'mrns': [
            {'mrn': '1234', 'site': 'TEST'},
        ],
    }

    patient = schemas.PatientSchema.model_validate(data)

    assert len(patient.mrns) == 1
    assert patient.date_of_death is None
    assert patient.health_insurance_number is None


def test_patient_mrns_non_empty() -> None:
    """The list of MRNs is required and cannot be an empty list."""
    data: dict[str, Any] = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': schemas.SexType.MALE,
        'date_of_birth': '1986-10-05',
        'health_insurance_number': None,
        'date_of_death': None,
    }

    with pytest.raises(ValidationError) as exc:
        schemas.PatientSchema.model_validate(data)

    assert exc.value.error_count() == 1
    assert exc.value.errors()[0]['loc'] == ('mrns',)
    assert exc.value.errors()[0]['type'] == 'missing'

    data.update({'mrns': []})

    with pytest.raises(ValidationError) as exc:
        schemas.PatientSchema.model_validate(data)

    assert exc.value.error_count() == 1
    assert exc.value.errors()[0]['loc'] == ('mrns',)
    assert exc.value.errors()[0]['type'] == 'too_short'


def test_patient_deceased() -> None:
    """The date of death is validated correctly."""
    data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': 'female',
        'date_of_birth': '1986-10-05',
        'health_insurance_number': 'SIMM86600599',
        'date_of_death': '2000-05-04 13:12',
        'mrns': [
            {'mrn': '1234', 'site': 'TEST'},
        ],
    }

    patient = schemas.PatientSchema.model_validate(data)

    assert patient.date_of_death
    assert patient.date_of_death.tzinfo is None


def test_patient_mrns() -> None:
    """The list of MRNs supports more than one element."""
    data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': 'female',
        'date_of_birth': '1986-10-05',
        'health_insurance_number': 'SIMM86600599',
        'date_of_death': None,
        'mrns': [
            {'mrn': '9999996', 'site': 'OMI'},
            {'mrn': '1234', 'site': 'OHIGPH'},
        ],
    }

    patient = schemas.PatientSchema.model_validate(data)

    assert len(patient.mrns) == 2


def test_patient_by_hin_request() -> None:
    """Test the PatientByHINSchema."""
    request = schemas.PatientByHINSchema(health_insurance_number='TEST')

    assert request.health_insurance_number == 'TEST'


def test_patient_by_mrn_request() -> None:
    """Test the PatientByMRNSchema."""
    request = schemas.PatientByMRNSchema(mrn='1234', site='TEST')

    assert request.mrn == '1234'
    assert request.site == 'TEST'
