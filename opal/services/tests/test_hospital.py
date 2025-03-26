
from typing import Dict, cast

from pytest_mock.plugin import MockerFixture

from ..hospital import OIECommunicationService

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
communicate_service = OIECommunicationService()


def test_find_patient_by_mrn_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was successful
    mock_oie_response = mocker.patch('opal.services.hospital.OIECommunicationService.find_patient_by_mrn')
    mock_oie_response.return_value = OIE_data

    response = communicate_service.find_patient_by_mrn('9999993', 'MGH')
    data = cast(Dict[str, dict], response)['data']
    assert data is not None


def test_find_patient_by_mrn_failure(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return None."""
    # mock find_patient_by_mrn and pretend it was failed
    mock_oie_response = mocker.patch('opal.services.hospital.OIECommunicationService.find_patient_by_mrn')
    mock_oie_response.return_value = None

    response = communicate_service.find_patient_by_mrn('9999993', 'MGH')
    assert response is None


def test_find_patient_by_ramq_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was successful
    mock_oie_response = mocker.patch('opal.services.hospital.OIECommunicationService.find_patient_by_ramq')
    mock_oie_response.return_value = OIE_data

    response = communicate_service.find_patient_by_ramq('AAAA9999999')
    data = cast(Dict[str, dict], response)['data']
    assert data is not None


def test_find_patient_by_ramq_failure(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return None."""
    # mock find_patient_by_mrn and pretend it was failed
    mock_oie_response = mocker.patch('opal.services.hospital.OIECommunicationService.find_patient_by_ramq')
    mock_oie_response.return_value = None

    response = communicate_service.find_patient_by_ramq('AAAA9999999')
    assert response is None
