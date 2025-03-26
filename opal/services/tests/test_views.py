
from pytest_mock.plugin import MockerFixture
from typing import Dict, cast

from .. import hospital

OIE_data = {
    'status': 'success',
    'data': {
        'dateOfBirth': '1953-01-01 00:00:00',
        'firstName': 'SANDRA',
        'lastName': 'TESTMUSEMGHPROD',
        'sex': 'F',
        'alias': '',
        'ramq': 'TESS53510111',
        'ramqExpiration': '2018-01-31 23:59:59',
        'mrns': [
            {
                'site': 'MGH',
                'mrn': '9999993',
                'active': True,
            },
        ],
    },
}


def test_find_patient_by_mrn_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was unsuccessful
    mock_oie_response = mocker.patch('opal.services.hospital.find_patient_by_mrn')
    mock_oie_response.return_value = OIE_data

    response = hospital.find_patient_by_mrn('9999993', 'MGH')
    status = cast(Dict[str, dict], response['status'])
    assert status == OIE_data['status']


def test_find_patient_by_mrn_failure(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was unsuccessful
    mock_oie_response = mocker.patch('opal.services.hospital.find_patient_by_mrn')
    mock_oie_response.return_value = None

    response = hospital.find_patient_by_mrn('9999993', 'MGH')
    assert response is None


def test_find_patient_by_ramq_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was unsuccessful
    mock_oie_response = mocker.patch('opal.services.hospital.find_patient_by_ramq')
    mock_oie_response.return_value = OIE_data

    response = hospital.find_patient_by_ramq('AAAA9999999')
    status = cast(Dict[str, dict], response['status'])
    assert status == OIE_data['status']


def test_find_patient_by_ramq_failure(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was unsuccessful
    mock_oie_response = mocker.patch('opal.services.hospital.find_patient_by_ramq')
    mock_oie_response.return_value = None

    response = hospital.find_patient_by_ramq('AAAA9999999')
    assert response is None
