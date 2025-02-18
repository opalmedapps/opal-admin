# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from http import HTTPStatus
from types import MappingProxyType
from typing import Any

from django.utils import timezone

import requests
from pytest_mock import MockerFixture

from opal.core.test_utils import RequestMockerTest
from opal.services.general.service_communication import SOURCE_SYSTEM_TIMEOUT
from opal.services.general.service_error import ServiceErrorHandler
from opal.services.hospital.hospital import (
    SourceSystemReportExportData,
    SourceSystemService,
)
from opal.services.hospital.hospital_communication import SourceSystemHTTPCommunicationManager
from opal.services.hospital.hospital_validation import SourceSystemValidator

ENCODING = 'utf-8'
BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
RAMQ_VALID = 'ABCD12345678'
RAMQ_INVALID = 'ABC123456789'
MRN = '9999996'
SITE_CODE = 'MUHC'
SOURCE_SYSTEM_CREDENTIALS_USER = 'questionnaire'
SOURCE_SYSTEM_CREDENTIALS = '12345Opal!!'
SOURCE_SYSTEM_HOST = 'https://localhost'

SOURCE_SYSTEM_PATIENT_DATA = MappingProxyType({
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

source_system_service = SourceSystemService()


def _create_report_export_response_data() -> dict[str, str]:
    """
    Create mock `dict` response on the `report export` HTTP POST request.

    Returns:
        mock data response
    """
    return {'status': 'success'}


def _create_source_system_service_mock_settings() -> SourceSystemService:
    """
    Create a mock SourceSystemService with specific parameters different from the default ones in settings.

    Returns:
        A mock SourceSystemService
    """
    # Create a communication manager with mock settings
    source_system_communication_mock = SourceSystemHTTPCommunicationManager()
    source_system_communication_mock.base_url = SOURCE_SYSTEM_HOST
    source_system_communication_mock.user = SOURCE_SYSTEM_CREDENTIALS_USER
    source_system_communication_mock.password = SOURCE_SYSTEM_CREDENTIALS

    # Assign the communication manager to a new source_system_service
    source_system_service_mock = SourceSystemService()
    source_system_service_mock.communication_manager = source_system_communication_mock
    return source_system_service_mock


# __init__


def test_init_types() -> None:
    """Ensure init function creates helper services of certain types."""
    assert isinstance(source_system_service.communication_manager, SourceSystemHTTPCommunicationManager)
    assert isinstance(source_system_service.error_handler, ServiceErrorHandler)
    assert isinstance(source_system_service.validator, SourceSystemValidator)


def test_init_not_none() -> None:
    """Ensure init function creates helper services that are not `None`."""
    assert source_system_service.communication_manager is not None
    assert source_system_service.error_handler is not None
    assert source_system_service.validator is not None


# export_pdf_report
def test_export_pdf_report(mocker: MockerFixture) -> None:
    """Ensure successful report export request returns json response with successful HTTP status."""
    # mock actual source system API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert report_data['status'] == 'success'

    mock_post.assert_called_once()
    post_data = json.loads(mock_post.call_args[1]['json'])

    assert list(post_data.keys()) == ['mrn', 'site', 'reportContent', 'docType', 'documentDate']


def test_export_pdf_report_error(mocker: MockerFixture) -> None:
    """Ensure export request failure is handled and does not result in an error."""
    # mock actual source system API call to raise a request error
    generated_report_data: dict[str, Any] = {
        'status': 'error',
        'data': {
            'message': 'Source system response format is not valid.',
        },
    }
    RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert report_data == {
        'status': 'error',
        'data': {
            'message': 'Source system response format is not valid.',
        },
    }


def test_export_pdf_report_response_invalid(mocker: MockerFixture) -> None:
    """Ensure invalid response is handled and does not result in an error."""
    # mock actual source system API call to raise a request error
    generated_report_data: dict[str, Any] = {
        'invalidStatus': 'error',
    }
    RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert report_data == {
        'status': 'error',
        'data': {
            'message': 'Source system response format is not valid.',
            'responseData': {
                'invalidStatus': 'error',
            },
        },
    }


def test_export_pdf_report_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure response json decode failure is handled and does not result in an error."""
    # mock actual source system API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST
    mock_post.return_value._content = 'test string'.encode(ENCODING)

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Expecting value: line 1 column 1 (char 0)'


def test_export_pdf_report_uses_settings(mocker: MockerFixture) -> None:
    """Ensure source system export report request uses report settings."""
    # Create a new source system service that uses the mocked settings
    source_system_service_mock = _create_source_system_service_mock_settings()

    # mock actual source system API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    report_data = source_system_service_mock.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert report_data['status'] == 'success'

    payload = json.dumps({
        'mrn': MRN,
        'site': SITE_CODE,
        'reportContent': BASE64_ENCODED_REPORT,
        'docType': DOCUMENT_NUMBER,
        'documentDate': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    # assert that the mock was called exactly once and that the call was with exactly the same
    # parameters as in the `export_pdf_report` post request.
    # Arguments: *args, **kwargs
    mock_post.assert_called_once_with(
        url=f'{SOURCE_SYSTEM_HOST}/report/post',
        auth=requests.auth.HTTPBasicAuth(SOURCE_SYSTEM_CREDENTIALS_USER, SOURCE_SYSTEM_CREDENTIALS),
        headers=None,
        json=payload,
        timeout=SOURCE_SYSTEM_TIMEOUT,
    )


def test_export_pdf_report_invalid_mrn(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid MRN is handled and does not result in an error."""
    # mock actual source system API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn='',
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_site(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid site is handled and does not result in an error."""
    # mock actual source system API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site='',
            base64_content=BASE64_ENCODED_REPORT,
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_base64(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid base64 content is handled and does not result in an error."""
    # mock actual source system API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content='',
            document_number=DOCUMENT_NUMBER,
            document_date=timezone.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'


def test_export_pdf_report_invalid_doc_type(mocker: MockerFixture) -> None:
    """Ensure report export request with invalid document type is handled and does not result in an error."""
    # mock actual source system API call
    generated_report_data = _create_report_export_response_data()
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    report_data = source_system_service.export_pdf_report(
        SourceSystemReportExportData(
            mrn=MRN,
            site=SITE_CODE,
            base64_content=BASE64_ENCODED_REPORT,
            document_number='invalid document type',
            document_date=timezone.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert report_data['status'] == 'error'
    assert report_data['data']['message'] == 'Provided request data are invalid.'
