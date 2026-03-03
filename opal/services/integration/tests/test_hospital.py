# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from http import HTTPStatus
from typing import Any

import pytest
import requests
from pydantic import ValidationError
from pytest_mock import MockFixture

from opal.services.integration import hospital, schemas


class _MockResponse(requests.Response):
    def __init__(self, status_code: HTTPStatus, data: Any) -> None:
        self.status_code = status_code
        self.data = data

    @property
    def content(self) -> Any:
        if isinstance(self.data, schemas.ErrorResponseSchema):
            return self.data.model_dump_json().encode()

        return json.dumps(self.data).encode()


def test_nonok_response_error_not_valid() -> None:
    """A validation error is raised if the error response data is not valid."""
    with pytest.raises(ValidationError) as exc:
        hospital.NonOKResponseError(_MockResponse(HTTPStatus.BAD_REQUEST, {}))

    assert exc.value.error_count() == 2


def test_find_patient_by_hin_non_ok(mocker: MockFixture) -> None:
    """A NonOKResponseError is raised if the response is not OK."""
    error = schemas.ErrorResponseSchema(status=HTTPStatus.BAD_REQUEST, message='error message')
    mocker.patch('requests.post', return_value=_MockResponse(HTTPStatus.BAD_REQUEST, error))

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.find_patient_by_hin('test')

    assert exc.value.error == error


def test_find_patient_by_hin_not_found(mocker: MockFixture) -> None:
    """A PatientNotFoundError is raised if the response returns status not found."""
    mocker.patch('requests.post', return_value=_MockResponse(HTTPStatus.NOT_FOUND, {}))

    with pytest.raises(hospital.PatientNotFoundError):
        hospital.find_patient_by_hin('test')


def test_find_patient_by_hin_not_valid(mocker: MockFixture) -> None:
    """A ValidationError is raised if the response data is not valid."""
    response = _MockResponse(HTTPStatus.OK, {'first_name': 'Hans', 'last_name': 'Wurst'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(ValidationError):
        hospital.find_patient_by_hin('test')


def test_find_patient_by_hin(mocker: MockFixture) -> None:
    """A patient is returned if found."""
    data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': 'female',
        'date_of_birth': '1986-10-05',
        'health_insurance_number': 'SIMM86600599',
        'date_of_death': None,
        'mrns': [
            {
                'mrn': '9999996',
                'site': 'OMI',
            },
        ],
    }
    response = _MockResponse(HTTPStatus.OK, data)
    mocker.patch('requests.post', return_value=response)

    patient = hospital.find_patient_by_hin('test')

    assert patient == schemas.PatientSchema.model_validate(data)


def test_find_patient_by_mrn_non_ok(mocker: MockFixture) -> None:
    """A NonOKResponseError is raised if the response is not OK."""
    error = schemas.ErrorResponseSchema(status=HTTPStatus.BAD_REQUEST, message='error message')
    mocker.patch('requests.post', return_value=_MockResponse(HTTPStatus.BAD_REQUEST, error))

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.find_patient_by_mrn('1234', 'test')

    assert exc.value.error == error


def test_find_patient_by_mrn_not_found(mocker: MockFixture) -> None:
    """A PatientNotFoundError is raised if the response returns status not found."""
    mocker.patch('requests.post', return_value=_MockResponse(HTTPStatus.NOT_FOUND, {}))

    with pytest.raises(hospital.PatientNotFoundError):
        hospital.find_patient_by_mrn('1234', 'test')


def test_find_patient_by_mrn_not_valid(mocker: MockFixture) -> None:
    """A ValidationError is raised if the response data is not valid."""
    response = _MockResponse(HTTPStatus.OK, {'first_name': 'Hans', 'last_name': 'Wurst'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(ValidationError):
        hospital.find_patient_by_mrn('1234', 'test')


def test_find_patient_by_mrn(mocker: MockFixture) -> None:
    """A patient is returned if found."""
    data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': 'female',
        'date_of_birth': '1986-10-05',
        'health_insurance_number': 'SIMM86600599',
        'date_of_death': None,
        'mrns': [
            {
                'mrn': '9999996',
                'site': 'OMI',
            },
        ],
    }
    response = _MockResponse(HTTPStatus.OK, data)
    mocker.patch('requests.post', return_value=response)

    patient = hospital.find_patient_by_mrn('1234', 'test')

    assert patient == schemas.PatientSchema.model_validate(data)


def test_notify_new_patient(mocker: MockFixture) -> None:
    """No error is raised if the response is OK."""
    response = _MockResponse(HTTPStatus.OK, data=None)
    mocker.patch('requests.post', return_value=response)

    hospital.notify_new_patient('1234', 'TEST')


def test_notify_new_patient_bad_request(mocker: MockFixture) -> None:
    """A NonOKResponseError is raised if the response is not OK."""
    response = _MockResponse(HTTPStatus.BAD_REQUEST, data={'status': 400, 'message': 'no no no'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.notify_new_patient('1234', 'TEST')

    assert exc.value.error.status == 400
    assert exc.value.error.message == 'no no no'


def test_notify_new_patient_not_found(mocker: MockFixture) -> None:
    """A NonOKResponseError is raised if the patient was not found."""
    response = _MockResponse(HTTPStatus.NOT_FOUND, data={'status': 404, 'message': 'not found'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(hospital.PatientNotFoundError):
        hospital.notify_new_patient('1234', 'TEST')


def test_add_questionnaire_report(mocker: MockFixture) -> None:
    """No error is raised if the response is OK."""
    response = _MockResponse(HTTPStatus.OK, data=None)
    mocker.patch('requests.post', return_value=response)

    hospital.add_questionnaire_report('1234', 'TEST', b'report')


def test_add_questionnaire_report_bad_request(mocker: MockFixture) -> None:
    """A NonOKResponseError is raised if the response is not OK."""
    response = _MockResponse(HTTPStatus.BAD_REQUEST, data={'status': 400, 'message': 'no no no'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.add_questionnaire_report('1234', 'TEST', b'report')

    assert exc.value.error.status == 400
    assert exc.value.error.message == 'no no no'


def test_add_questionnaire_report_not_found(mocker: MockFixture) -> None:
    """A NonOKResponseError is raised if the patient was not found."""
    response = _MockResponse(HTTPStatus.NOT_FOUND, data={'status': 404, 'message': 'not found'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(hospital.PatientNotFoundError):
        hospital.add_questionnaire_report('1234', 'TEST', b'report')
