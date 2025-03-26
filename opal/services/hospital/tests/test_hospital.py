import json
import logging
from datetime import datetime
from http import HTTPStatus
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests
from _pytest.logging import LogCaptureFixture  # noqa: WPS436
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from requests.exceptions import RequestException

from opal.core.test_utils import RequestMockerTest
from opal.services.general.service_error import ServiceErrorHandler
from opal.services.hospital.hospital import OIEMRNData, OIEPatientData, OIEReportExportData, OIEService
from opal.services.hospital.hospital_communication import OIEHTTPCommunicationManager
from opal.services.hospital.hospital_validation import OIEValidator

ENCODING = 'utf-8'
BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
RAMQ_VALID = 'ABCD12345678'
RAMQ_INVALID = 'ABC123456789'
MRN = '9999996'
SITE_CODE = 'MUHC'
OIE_CREDENTIALS_USER = 'questionnaire'
OIE_CREDENTIALS = '12345Opal!!'
OIE_HOST = 'https://localhost'

OIE_PATIENT_DATA = MappingProxyType({
    'dateOfBirth': '1953-01-01',
    'firstName': 'SANDRA',
    'lastName': 'TESTMUSEMGHPROD',
    'sex': 'F',
    'alias': '',
    'deceased': True,
    'deathDateTime': '2023-01-01 00:00:00',
    'ramq': 'TESS53510111',
    'ramqExpiration': '201801',
    'mrns': [
        {
            'site': 'MGH',
            'mrn': '9999993',
            'active': True,
        },
    ],
})

oie_service = OIEService()


def _create_report_export_response_data() -> dict[str, str]:
    """Create mock `dict` response on the `report export` HTTP POST request.

    Returns:
        dict[str, str]: mock data response
    """
    return {'status': 'success'}


def _create_oie_service_mock_settings() -> OIEService:
    """Create a mock OIEService with specific parameters different from the default ones in settings.

    Returns:
        A mock OIEService
    """
    # Create a communication manager with mock settings
    oie_communication_mock = OIEHTTPCommunicationManager()
    oie_communication_mock.base_url = OIE_HOST
    oie_communication_mock.user = OIE_CREDENTIALS_USER
    oie_communication_mock.password = OIE_CREDENTIALS

    # Assign the communication manager to a new oie_service
    oie_service_mock = OIEService()
    oie_service_mock.communication_manager = oie_communication_mock
    return oie_service_mock


# __init__

def test_init_types() -> None:
    """Ensure init function creates helper services of certain types."""
    assert isinstance(oie_service.communication_manager, OIEHTTPCommunicationManager)
    assert isinstance(oie_service.error_handler, ServiceErrorHandler)
    assert isinstance(oie_service.validator, OIEValidator)


def test_init_not_none() -> None:
    """Ensure init function creates helper services that are not `None`."""
    assert oie_service.communication_manager is not None
    assert oie_service.error_handler is not None
    assert oie_service.validator is not None


# export_pdf_report
def test_export_pdf_report(mocker: MockerFixture) -> None:
    """Ensure successful report export request returns json response with successful HTTP status."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert report_data['status'] == 'success'

    mock_post.assert_called_once()
    post_data = json.loads(mock_post.call_args[1]['json'])

    assert list(post_data.keys()) == ['mrn', 'site', 'reportContent', 'docType', 'documentDate']


def test_export_pdf_report_error(mocker: MockerFixture) -> None:
    """Ensure export request failure is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    generated_report_data: dict[str, Any] = {
        'status': 'error',
        'data': {
            'message': 'OIE response format is not valid.',
        },
    }
    RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert report_data == {
        'status': 'error',
        'data': {
            'message': 'OIE response format is not valid.',
        },
    }


def test_export_pdf_report_response_invalid(mocker: MockerFixture) -> None:
    """Ensure invalid response is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    generated_report_data: dict[str, Any] = {
        'invalidStatus': 'error',
    }
    RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert report_data == {
        'status': 'error',
        'data': {
            'message': 'OIE response format is not valid.',
            'responseData': {
                'invalidStatus': 'error',
            },
        },
    }


def test_export_pdf_report_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure response json decode failure is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST
    mock_post.return_value._content = 'test string'.encode(ENCODING)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Expecting value: line 1 column 1 (char 0)'


def test_export_pdf_report_uses_settings(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """Ensure OIE export report request uses report settings."""
    # Create a new OIE service that uses the mocked settings
    oie_service_mock = _create_oie_service_mock_settings()

    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = oie_service_mock.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert report_data['status'] == 'success'

    payload = json.dumps({
        'mrn': MRN,
        'site': SITE_CODE,
        'reportContent': BASE64_ENCODED_REPORT,
        'docType': DOCUMENT_NUMBER,
        'documentDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    # assert that the mock was called exactly once and that the call was with exactly the same
    # parameters as in the `export_pdf_report` post request.
    # Arguments: *args, **kwargs
    mock_post.assert_called_once_with(
        url='{0}{1}'.format(OIE_HOST, '/report/post'),
        auth=requests.auth.HTTPBasicAuth(OIE_CREDENTIALS_USER, OIE_CREDENTIALS),
        headers=None,
        json=payload,
        timeout=5,
    )


def test_export_pdf_report_invalid_mrn(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid MRN is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn='',
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_site(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid site is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site='',
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_base64(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid base64 content is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content='',
            document_number=DOCUMENT_NUMBER,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_doc_type(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid document type is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number='invalid document type',
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_find_patient_by_mrn_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return the expected OIE data structure."""
    # mock find_patient_by_mrn and pretend it was successful
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': dict(OIE_PATIENT_DATA),
        },
    )

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d',
        ).date(),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=datetime.strptime(
            str(OIE_PATIENT_DATA['deathDateTime']),
            '%Y-%m-%d %H:%M:%S',
        ),
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=datetime.strptime(
            str(OIE_PATIENT_DATA['ramqExpiration']),
            '%Y%m',
        ),
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def test_find_by_mrn_empty_value_in_response(mocker: MockerFixture) -> None:
    """Ensure that None value in response returned from find_patient_by_mrn."""
    oie_patient_data_copy = OIE_PATIENT_DATA.copy()
    oie_patient_data_copy.update(deathDateTime='', ramqExpiration='')
    # mock find_patient_by_mrn and pretend it was successful
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': oie_patient_data_copy,
        },
    )

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d',
        ).date(),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=None,
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=None,
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def test_find_by_mrn_patient_not_found(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn handles the not found error accordingly."""
    # mock find_patient_by_mrn and pretend it was successful
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'error',
            'message': 'Patient not found',
        },
    )

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)
    assert response['status'] == 'error'
    assert response['data']['message'] == ['not_found']


def test_find_by_mrn_patient_not_test_patient(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn handles the not a test patient error accordingly."""
    # mock find_patient_by_mrn and pretend it was successful
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'error',
            'message': 'Not Opal test patient',
        },
    )

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)
    assert response['status'] == 'error'
    assert response['data']['message'] == ['no_test_patient']


def test_find_by_ramq_patient_not_found(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn handles the not found error accordingly."""
    # mock find_patient_by_mrn and pretend it was successful
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'error',
            'message': 'Patient not found',
        },
    )

    response = oie_service.find_patient_by_ramq('SIMM86100199')
    assert response['status'] == 'error'
    assert response['data']['message'] == ['not_found']


@patch('requests.post')
def test_find_patient_by_mrn_failure(post_mock: MagicMock, caplog: LogCaptureFixture, mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_mrn return None and log the error."""
    # mock the post request and pretend it raises `RequestException`
    post_mock.side_effect = RequestException('Caused by ConnectTimeoutError.')

    with pytest.raises(RequestException):  # noqa: PT012
        with caplog.at_level(logging.ERROR):
            post_mock()

    response = oie_service.find_patient_by_mrn(MRN, SITE_CODE)

    # assert user error message
    assert response['status'] == 'error'
    assert response['data'] == {
        'message': ['connection_error'],
        'responseData': {
            'status': 'error',
            'data': {
                'message': 'Caused by ConnectTimeoutError.',
                'exception': mocker.ANY,
            },
        },
    }

    # assert exception and system error message
    assert caplog.records[0].message == 'OIE error: Caused by ConnectTimeoutError.'
    assert caplog.records[0].levelname == 'ERROR'


def test_find_patient_by_mrn_invalid_mrn(mocker: MockerFixture) -> None:
    """Ensure find_patient_by_mrn request with invalid MRN is handled and does not result in an error."""
    response = oie_service.find_patient_by_mrn('', SITE_CODE)
    assert response['status'] == 'error'
    assert response['data']['message'] == 'Provided MRN or site is invalid.'


def test_find_patient_by_mrn_invalid_site(mocker: MockerFixture) -> None:
    """Ensure find_patient_by_mrn request with invalid site is handled and does not result in an error."""
    response = oie_service.find_patient_by_mrn(MRN, '')
    assert response['status'] == 'error'
    assert response['data']['message'] == 'Provided MRN or site is invalid.'


def test_find_patient_by_ramq_success(mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return the expected OIE data structure."""
    # mock find_patient_by_ramq and pretend it was successful
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': dict(OIE_PATIENT_DATA),
        },
    )

    response = oie_service.find_patient_by_ramq(RAMQ_VALID)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d',
        ).date(),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=datetime.strptime(
            str(OIE_PATIENT_DATA['deathDateTime']),
            '%Y-%m-%d %H:%M:%S',
        ),
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=datetime.strptime(
            str(OIE_PATIENT_DATA['ramqExpiration']),
            '%Y%m',
        ),
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


def test_empty_value_in_response_by_ramq(mocker: MockerFixture) -> None:
    """Ensure that None value in response returned from find_patient_by_ramq."""
    oie_patient_data_copy = OIE_PATIENT_DATA.copy()
    oie_patient_data_copy.update(deathDateTime='', ramqExpiration='')
    # mock find_patient_by_ramq and pretend it was successful
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'success',
            'data': oie_patient_data_copy,
        },
    )

    response = oie_service.find_patient_by_ramq(RAMQ_VALID)
    assert response['status'] == 'success'
    assert response['data'] == OIEPatientData(
        date_of_birth=datetime.strptime(
            str(OIE_PATIENT_DATA['dateOfBirth']),
            '%Y-%m-%d',
        ).date(),
        first_name=str(OIE_PATIENT_DATA['firstName']),
        last_name=str(OIE_PATIENT_DATA['lastName']),
        sex=str(OIE_PATIENT_DATA['sex']),
        alias=str(OIE_PATIENT_DATA['alias']),
        deceased=bool(OIE_PATIENT_DATA['deceased']),
        death_date_time=None,
        ramq=str(OIE_PATIENT_DATA['ramq']),
        ramq_expiration=None,
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )


@patch('requests.post')
def test_find_patient_by_ramq_failure(post_mock: MagicMock, caplog: LogCaptureFixture, mocker: MockerFixture) -> None:
    """Ensure that find_patient_by_ramq return None and log the error."""
    # mock the post request and pretend it raises `RequestException`
    post_mock.side_effect = RequestException('Caused by ConnectTimeoutError.')

    with pytest.raises(RequestException):  # noqa: PT012
        with caplog.at_level(logging.ERROR):
            post_mock()

    response = oie_service.find_patient_by_ramq(RAMQ_VALID)

    # assert user error message
    assert response['status'] == 'error'
    assert response['data'] == {
        'message': ['connection_error'],
        'responseData': {
            'status': 'error',
            'data': {
                'message': 'Caused by ConnectTimeoutError.',
                'exception': mocker.ANY,
            },
        },
    }

    # assert exception and system error message
    assert caplog.records[0].message == 'OIE error: Caused by ConnectTimeoutError.'
    assert caplog.records[0].levelname == 'ERROR'


def test_find_patient_by_ramq_invalid_ramq(mocker: MockerFixture) -> None:
    """Ensure find_patient_by_ramq request with invalid ramq is handled and does not result in an error."""
    # mock find_patient_by_mrn and pretend it was failed
    RequestMockerTest.mock_requests_post(mocker, {'status': 'success'})

    response = oie_service.find_patient_by_ramq(RAMQ_INVALID)
    assert response['status'] == 'error'
    assert response['data']['message'] == 'Provided RAMQ is invalid.'


def test_new_opal_patient_success(mocker: MockerFixture) -> None:
    """Ensure that set_opal_patient can succeed."""
    RequestMockerTest.mock_requests_post(mocker, {'status': 'success'})

    response = oie_service.new_opal_patient(
        [
            ('RVH', '0000001'),
            ('MCH', '0000002'),
        ],
    )

    assert response['status'] == 'success'
    assert not hasattr(response, 'data')


def test_new_opal_patient_empty_input(mocker: MockerFixture) -> None:
    """Ensure that set_opal_patient fails gracefully when given an empty MRN list."""
    RequestMockerTest.mock_requests_post(mocker, {'status': 'success'})

    response = oie_service.new_opal_patient([])

    assert response['status'] == 'error'
    assert 'A list of active (site, mrn) tuples should be provided' in response['data']['message']


def test_new_opal_patient_error(mocker: MockerFixture) -> None:
    """Ensure that set_opal_patient returns an error for invalid input."""
    RequestMockerTest.mock_requests_post(
        mocker,
        {
            'status': 'error',
            'error': 'Some error message',
        },
    )

    response = oie_service.new_opal_patient(
        [
            ('RVH', '0000001'),
            ('MCH', '0000002'),
        ],
    )

    assert response['status'] == 'error'
    assert response['data']['responseData']['error'] == 'Some error message'
