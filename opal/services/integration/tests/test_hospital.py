import json
from http import HTTPStatus
from typing import Any

import pytest
import requests
from pydantic import ValidationError
from pytest_mock import MockFixture

from opal.services.integration import hospital, models


class _MockResponse(requests.Response):
    def __init__(self, status_code: HTTPStatus, data: Any) -> None:
        self.status_code = status_code
        self.data = data

    @property
    def content(self) -> Any:
        if isinstance(self.data, models.ErrorResponse):
            return self.data.model_dump_json().encode()

        return json.dumps(self.data).encode()


def test_nonok_response_error_not_valid() -> None:
    with pytest.raises(ValidationError) as exc:
        hospital.NonOKResponseError(_MockResponse(HTTPStatus.BAD_REQUEST, {}))

    assert exc.value.error_count() == 2


def test_find_patient_by_hin_non_ok(mocker: MockFixture) -> None:
    error = models.ErrorResponse(status_code=HTTPStatus.BAD_REQUEST, message='error message')
    mocker.patch('requests.post', return_value=_MockResponse(HTTPStatus.BAD_REQUEST, error))

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.find_patient_by_hin('test')

    assert exc.value.error == error


def test_find_patient_by_hin_not_valid(mocker: MockFixture) -> None:
    response = _MockResponse(HTTPStatus.OK, {'first_name': 'Hans', 'last_name': 'Wurst'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(ValidationError):
        hospital.find_patient_by_hin('test')


def test_find_patient_by_hin(mocker: MockFixture) -> None:
    data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': 'female',
        'date_of_birth': '1986-10-05',
        'health_insurance_number': 'SIMM86600599',
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

    assert patient == models.Patient.model_validate(data)


def test_find_patient_by_mrn_non_ok(mocker: MockFixture) -> None:
    error = models.ErrorResponse(status_code=HTTPStatus.BAD_REQUEST, message='error message')
    mocker.patch('requests.post', return_value=_MockResponse(HTTPStatus.BAD_REQUEST, error))

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.find_patient_by_mrn('1234', 'test')

    assert exc.value.error == error


def test_find_patient_by_mrn_not_valid(mocker: MockFixture) -> None:
    response = _MockResponse(HTTPStatus.OK, {'first_name': 'Hans', 'last_name': 'Wurst'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(ValidationError):
        hospital.find_patient_by_mrn('1234', 'test')


def test_find_patient_by_mrn(mocker: MockFixture) -> None:
    data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'sex': 'female',
        'date_of_birth': '1986-10-05',
        'health_insurance_number': 'SIMM86600599',
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

    assert patient == models.Patient.model_validate(data)


def test_notify_new_patient(mocker: MockFixture) -> None:
    response = _MockResponse(HTTPStatus.OK, data=None)
    mocker.patch('requests.post', return_value=response)

    hospital.notify_new_patient('1234', 'TEST')


def test_notify_new_patient_bad_request(mocker: MockFixture) -> None:
    response = _MockResponse(HTTPStatus.BAD_REQUEST, data={'status_code': 400, 'message': 'no no no'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.notify_new_patient('1234', 'TEST')

    assert exc.value.error.status_code == 400
    assert exc.value.error.message == 'no no no'


def test_notify_new_patient_not_found(mocker: MockFixture) -> None:
    response = _MockResponse(HTTPStatus.BAD_REQUEST, data={'status_code': 404, 'message': 'not found'})
    mocker.patch('requests.post', return_value=response)

    with pytest.raises(hospital.NonOKResponseError) as exc:
        hospital.notify_new_patient('1234', 'TEST')

    assert exc.value.error.status_code == 404
    assert exc.value.error.message == 'not found'
