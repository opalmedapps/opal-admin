import json
from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from requests import RequestException, Response
from requests.auth import HTTPBasicAuth

from opal.services.hospital import OIECommunicationService, OIEReportExportData

ENCODING = 'utf-8'
BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
MRN = '9999996'
SITE_CODE = 'MUHC'
OIE_CREDENTIALS_USER = 'questionnaire'
OIE_CREDENTIALS = '12345Opal!!'
OIE_HOST = 'https://localhost/'

oie_service = OIECommunicationService()

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def _create_report_export_response_data() -> dict[str, str]:
    return {'status': 'success'}


def _mock_requests_post(
    mocker: MockerFixture,
    generated_report_export_response_data: dict[str, str],
) -> MagicMock:
    # mock actual web API call
    mock_post = mocker.patch('requests.post')
    response = Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(generated_report_export_response_data).encode(ENCODING)
    mock_post.return_value = response

    return mock_post


# _is_report_export_data_valid

def test_is_report_export_data_valid_success() -> None:
    """Ensure `OIEReportExportData` successfully validates."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data)


def test_is_report_export_data_invalid_mrn() -> None:
    """Ensure `OIEReportExportData` with invalid MRN are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn='',
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


def test_is_report_export_data_invalid_site() -> None:
    """Ensure `OIEReportExportData` with invalid site are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site='',
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


def test_is_report_export_data_invalid_content() -> None:
    """Ensure `OIEReportExportData` with invalid base64 content are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content='INVALID CONTENT',
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


def test_is_report_export_data_invalid_doc_type() -> None:
    """Ensure `OIEReportExportData` with invalid document type are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number='FU-INVALID DOCUMENT TYPE',
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


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
    assert json.loads(report_data.content)['status'] == 'success'

    mock_post.assert_called_once()
    post_data = json.loads(mock_post.call_args[1]['json'])

    assert list(post_data.keys()) == ['mrn', 'site', 'reportContent', 'docType', 'documentDate']


def test_export_pdf_report_error(mocker: MockerFixture) -> None:
    """Ensure export request failure is handled and does not result in an error."""
    # mock actual OIE API call to raise a request error
    generated_report_data: dict[str, str] = {}
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.side_effect = RequestException('request failed')
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

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
    assert json.loads(report_data.content) == {'status': HTTPStatus.BAD_REQUEST, 'message': 'request failed'}


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
    assert json.loads(report_data.content)['status'] == HTTPStatus.BAD_REQUEST
    assert json.loads(report_data.content)['message'] == 'Expecting value: line 1 column 1 (char 0)'


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

    assert report_data.status_code == HTTPStatus.OK

    payload = json.dumps({
        'mrn': MRN,
        'site': SITE_CODE,
        'reportContent': BASE64_ENCODED_REPORT,
        'docType': DOCUMENT_NUMBER,
        'documentDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    mock_post.assert_called_once_with(
        '{0}{1}'.format(OIE_HOST, 'reports/post'),
        json=payload,
        auth=HTTPBasicAuth(OIE_CREDENTIALS_USER, OIE_CREDENTIALS),
        timeout=5,
        verify=False,
    )


def test_export_pdf_report_ivalid_mrn(mocker: MockerFixture) -> None:
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
    assert json.loads(report_data.content)['status'] == HTTPStatus.BAD_REQUEST
    assert json.loads(report_data.content)['message'] == 'invalid export data'


def test_export_pdf_report_ivalid_site(mocker: MockerFixture) -> None:
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
    assert json.loads(report_data.content)['status'] == HTTPStatus.BAD_REQUEST
    assert json.loads(report_data.content)['message'] == 'invalid export data'


def test_export_pdf_report_ivalid_base64(mocker: MockerFixture) -> None:
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
    assert json.loads(report_data.content)['status'] == HTTPStatus.BAD_REQUEST
    assert json.loads(report_data.content)['message'] == 'invalid export data'


def test_export_pdf_report_ivalid_doc_type(mocker: MockerFixture) -> None:
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
    assert json.loads(report_data.content)['status'] == HTTPStatus.BAD_REQUEST
    assert json.loads(report_data.content)['message'] == 'invalid export data'
