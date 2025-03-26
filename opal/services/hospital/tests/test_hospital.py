import json
from datetime import datetime
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock

import requests
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture

from opal.services.hospital.hospital import OIEReportExportData, OIEService
from opal.services.hospital.hospital_communication import OIEHTTPCommunicationManager
from opal.services.hospital.hospital_error import OIEErrorHandler
from opal.services.hospital.hospital_validation import OIEValidator

ENCODING = 'utf-8'
BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
MRN = '9999996'
SITE_CODE = 'MUHC'
OIE_CREDENTIALS_USER = 'questionnaire'
OIE_CREDENTIALS = '12345Opal!!'
OIE_HOST = 'https://localhost'

oie_service = OIEService()


def _create_report_export_response_data() -> dict[str, str]:
    """Create mock `dict` response on the `report export` HTTP POST request.

    Returns:
        dict[str, str]: mock data response
    """
    return {'status': 'success'}


def _mock_requests_post(
    mocker: MockerFixture,
    generated_report_export_response_data: dict[str, str],
) -> MagicMock:
    """Mock actual HTTP POST web API call to the OIE.

    Args:
        mocker (MockerFixture): object that provides the same interface to functions in the mock module
        generated_report_export_response_data (dict[str, str]): generated mock response data

    Returns:
        MagicMock: object that mocks HTTP post request to the OIE for exporting reports
    """
    mock_post = mocker.patch('requests.post')
    response = requests.Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(generated_report_export_response_data).encode(ENCODING)
    mock_post.return_value = response

    return mock_post


# __init__

def test_init_types() -> None:
    """Ensure init function creates helper services of certain types."""
    assert isinstance(oie_service.communication_manager, OIEHTTPCommunicationManager)
    assert isinstance(oie_service.error_handler, OIEErrorHandler)
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
    mock_post = _mock_requests_post(mocker, generated_report_data)

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
    _mock_requests_post(mocker, generated_report_data)

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
    _mock_requests_post(mocker, generated_report_data)

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
    mock_post = _mock_requests_post(mocker, generated_report_data)
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
    settings.OIE_USER = OIE_CREDENTIALS_USER
    settings.OIE_PASSWORD = OIE_CREDENTIALS
    settings.OIE_HOST = OIE_HOST

    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
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
        url='{0}{1}'.format(OIE_HOST, ':6682/reports/post'),
        auth=requests.auth.HTTPBasicAuth(OIE_CREDENTIALS_USER, OIE_CREDENTIALS),
        headers=None,
        json=payload,
        timeout=5,
        verify=False,
    )


def test_export_pdf_report_invalid_mrn(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid MRN is handled and does not result in an error."""
    # mock actual OIE API call
    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)
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
    mock_post = _mock_requests_post(mocker, generated_report_data)

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
    mock_post = _mock_requests_post(mocker, generated_report_data)
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
    mock_post = _mock_requests_post(mocker, generated_report_data)
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
