# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import base64
import datetime as dt
from typing import Any

import pytest
from pydantic import ValidationError

from .. import schemas


def test_error_response() -> None:
    """Test the ErrorResponseSchema."""
    response = schemas.ErrorResponseSchema(status=404, message='Patient not found')

    assert response.status == 404
    assert response.message == 'Patient not found'


def test_hospital_number() -> None:
    """Test the HospitalNumberSchema."""
    hospital_number = schemas.HospitalNumberSchema(mrn='1234', site='TEST')

    assert hospital_number.mrn == '1234'
    assert hospital_number.site == 'TEST'
    assert hospital_number.is_active is True


def test_hospital_number_inactive() -> None:
    """Test the HospitalNumberSchema with inactive status."""
    hospital_number = schemas.HospitalNumberSchema(mrn='1234', site='TEST', is_active=False)

    assert hospital_number.is_active is False


def test_hospital_number_non_empty() -> None:
    """MRN and site cannot be empty."""
    with pytest.raises(ValidationError) as exc:
        schemas.HospitalNumberSchema(mrn='', site='')

    assert exc.value.error_count() == 2


@pytest.mark.parametrize('sex', schemas.SexTypeSchema)
def test_patient_minimal(sex: schemas.SexTypeSchema) -> None:
    """Test the PatientSchema with minimal data."""
    data: dict[str, Any] = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': sex.value,
        'date_of_birth': '1986-10-05',
        'date_of_death': None,
        'health_insurance_number': 'TEST',
        'mrns': [],
    }

    patient = schemas.PatientSchema.model_validate(data)

    assert len(patient.mrns) == 0
    assert patient.date_of_death is None
    assert patient.health_insurance_number == 'TEST'


def test_patient_medical_number_required() -> None:
    """The health insurance number or at least one MRN is required."""
    data: dict[str, Any] = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': schemas.SexTypeSchema.MALE,
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
    assert exc.value.errors()[0]['loc'] == ()
    assert exc.value.errors()[0]['type'] == 'value_error'
    assert 'Patient must have at least one medical number' in exc.value.errors()[0]['msg']


def test_patient_mrn_only() -> None:
    """The health insurance number is not required if at least one MRN is given."""
    data: dict[str, Any] = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': schemas.SexTypeSchema.MALE,
        'date_of_birth': '1986-10-05',
        'health_insurance_number': None,
        'date_of_death': None,
        'mrns': [
            {'mrn': '1234', 'site': 'TEST'},
        ],
    }

    schemas.PatientSchema.model_validate(data)


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
            {'mrn': '4321', 'site': 'OHIGPH', 'is_active': False},
        ],
    }

    patient = schemas.PatientSchema.model_validate(data)

    assert len(patient.mrns) == 3


def test_patient_by_hin_request() -> None:
    """Test the PatientByHINSchema."""
    request = schemas.PatientByHINSchema(health_insurance_number='TEST')

    assert request.health_insurance_number == 'TEST'


def test_patient_by_mrn_request() -> None:
    """Test the PatientByMRNSchema."""
    request = schemas.PatientByMRNSchema(mrn='1234', site='TEST')

    assert request.mrn == '1234'
    assert request.site == 'TEST'


def test_questionnaire_report_request() -> None:
    """Test the QuestionnaireReportRequestSchema."""
    content = b'test'
    request = schemas.QuestionnaireReportRequestSchema(
        mrn='1234',
        site='TEST',
        document=base64.b64encode(content),
        document_datetime=dt.datetime.now(dt.UTC),
    )

    assert request.mrn == '1234'
    assert request.site == 'TEST'
    assert request.document == content
    assert request.document_datetime.tzinfo is not None


def test_questionnaire_report_request_aware() -> None:
    """Test the QuestionnaireReportRequestSchema with a native datetime."""
    content = b'test'

    with pytest.raises(ValidationError) as exc:
        schemas.QuestionnaireReportRequestSchema(
            mrn='1234',
            site='TEST',
            document=base64.b64encode(content),
            document_datetime=dt.datetime.now(),  # noqa: DTZ005
        )

    assert exc.value.error_count() == 1
    assert exc.value.errors()[0]['loc'] == ('document_datetime',)
    assert exc.value.errors()[0]['type'] == 'timezone_aware'


def test_questionnaire_report_request_base64() -> None:
    """Test the QuestionnaireReportRequestSchema with an invalid base64 encoded string."""
    content = b'unencodable'

    with pytest.raises(ValidationError) as exc:
        schemas.QuestionnaireReportRequestSchema(
            mrn='1234',
            site='TEST',
            document=content,
            document_datetime=dt.datetime.now(dt.UTC),
        )

    assert exc.value.error_count() == 1
    assert exc.value.errors()[0]['loc'] == ('document',)
    assert exc.value.errors()[0]['type'] == 'base64_decode'
