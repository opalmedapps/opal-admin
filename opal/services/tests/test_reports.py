import json
from http import HTTPStatus
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture  # noqa: WPS436
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from requests.exceptions import RequestException

from opal.core.test_utils import RequestMockerTest
from opal.patients import factories as patient_factories
from opal.services.reports import QuestionnaireReportRequestData, ReportService
from opal.utils.base64 import Base64Util

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])

BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
ENCODING = 'utf-8'
LOGO_PATH = Path('opal/tests/fixtures/test_logo.png')
NON_STRING_VALUE = 123
TEST_LEGACY_QUESTIONNAIRES_REPORT_URL = 'http://localhost:80/report'

reports_service = ReportService()

QUESTIONNAIRE_REPORT_REQUEST_DATA = QuestionnaireReportRequestData(
    patient_id=51,
    patient_name='Bart Simpson',
    patient_site='RVH',
    patient_mrn='9999996',
    logo_path=LOGO_PATH,
    language='en',
)


def _create_generated_report_data(status: HTTPStatus) -> dict[str, dict[str, str]]:
    """Create mock `dict` response on the `report` HTTP POST request.

    Args:
        status: response status code

    Returns:
        mock data response
    """
    return {
        'data': {
            'status': 'Success: {0}'.format(status),
            'base64EncodedReport': BASE64_ENCODED_REPORT,
        },
    }


# _is_questionnaire_report_request_data_valid

def test_is_questionnaire_report_data_valid() -> None:
    """Ensure `QuestionnaireReportRequestData` successfully validates."""
    assert reports_service._is_questionnaire_report_request_data_valid(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )


def test_is_questionnaire_report_invalid_patient() -> None:
    """Ensure invalid `QuestionnaireReportRequestData` (invalid patient) are handled and does not result in an error."""
    report_data = QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
        patient_id=-1,
    )

    assert reports_service._is_questionnaire_report_request_data_valid(report_data) is False


def test_is_questionnaire_report_invalid_logo() -> None:
    """Ensure invalid `QuestionnaireReportRequestData` (invalid logo) are handled and does not result in an error."""
    report_data = QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
        logo_path=Path('invalid/logo/path'),
    )

    assert reports_service._is_questionnaire_report_request_data_valid(report_data) is False


def test_is_questionnaire_report_invalid_language() -> None:
    """Ensure invalid `QuestionnaireReportRequestData` (invalid language) are handled without errors."""
    report_data = QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
        language='invalid_language',
    )

    assert reports_service._is_questionnaire_report_request_data_valid(report_data) is False


# _request_base64_report function tests

def test_request_base64_report(mocker: MockerFixture) -> None:
    """Ensure successful report request returns base64 encoded pdf report."""
    patient_factories.HospitalPatient(
        site=patient_factories.Site(code='RVH'),
    )
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    response_base64_report = reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert response_base64_report == BASE64_ENCODED_REPORT

    mock_post.assert_called_once()
    post_data = json.loads(mock_post.call_args[1]['data'])

    assert list(post_data.keys()) == [
        'patient_id',
        'patient_name',
        'patient_site',
        'patient_mrn',
        'logo_base64',
        'language',
    ]


def test_request_base64_report_error(mocker: MockerFixture) -> None:
    """Ensure request failure is handled and does not result in an error."""
    # mock actual web API call to raise a request error
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.side_effect = RequestException('request failed')

    base64_report = reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_bad_request(mocker: MockerFixture) -> None:
    """Ensure request failure (bad request response) is handled and does not result in an error."""
    # mock actual web API call to raise a request error
    generated_report_data = _create_generated_report_data(HTTPStatus.BAD_REQUEST)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    base64_report = reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert base64_report is None


def test_request_base64_report_json_key_error(mocker: MockerFixture) -> None:
    """Ensure response json key failure is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value._content = json.dumps({}).encode(ENCODING)

    base64_report = reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure response json decode failure is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value._content = 'test string'.encode(ENCODING)

    base64_report = reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_is_string(mocker: MockerFixture) -> None:
    """Ensure returned base64EncodedReport value is a string."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert isinstance(base64_report, str)


def test_request_base64_report_not_string(mocker: MockerFixture) -> None:
    """Ensure returned base64EncodedReport non-string value is handled and does not result in an error."""
    patient_factories.HospitalPatient(
        site=patient_factories.Site(code='RVH'),
    )
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    data = _create_generated_report_data(HTTPStatus.OK)
    data['data']['base64EncodedReport'] = NON_STRING_VALUE  # type: ignore[assignment]
    mock_post.return_value._content = json.dumps(data).encode(ENCODING)

    base64_report = reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_request_base64_report_uses_settings(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """Ensure base64 report request uses report settings."""
    settings.LEGACY_QUESTIONNAIRES_REPORT_URL = TEST_LEGACY_QUESTIONNAIRES_REPORT_URL

    # mock actual web API call
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.OK

    reports_service._request_base64_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK

    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({
        'patient_id': 51,
        'patient_name': 'Bart Simpson',
        'patient_site': 'RVH',
        'patient_mrn': '9999996',
        'logo_base64': Base64Util().encode_to_base64(LOGO_PATH),
        'language': 'en',
    })
    mock_post.assert_called_once_with(
        url=TEST_LEGACY_QUESTIONNAIRES_REPORT_URL,
        headers=headers,
        data=payload,
        timeout=60,
    )


# generate_questionnaire_report function tests

def test_questionnaire_report(mocker: MockerFixture) -> None:
    """Ensure the returned value is base64 encoded pdf report."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = reports_service.generate_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert Base64Util().is_base64(base64_report)
    assert base64_report == BASE64_ENCODED_REPORT


def test_questionnaire_report_error(mocker: MockerFixture) -> None:
    """Ensure function failure is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.BAD_REQUEST)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    base64_report = reports_service.generate_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            patient_id=-1,
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert base64_report is None


def test_questionnaire_report_invalid_patient(mocker: MockerFixture) -> None:
    """Ensure invalid patient id is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = reports_service.generate_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            patient_id=-1,
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_questionnaire_report_invalid_logo(mocker: MockerFixture) -> None:
    """Ensure invalid logo path is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = reports_service.generate_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            logo_path=Path('invalid/logo/path'),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_questionnaire_report_invalid_language(mocker: MockerFixture) -> None:
    """Ensure invalid language is handled and does not result in an error."""
    generated_report_data = _create_generated_report_data(HTTPStatus.OK)
    mock_post = RequestMockerTest.mock_requests_post(mocker, generated_report_data)

    base64_report = reports_service.generate_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA._replace(
            language='invalid language',
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None


def test_questionnaire_report_no_base64(mocker: MockerFixture, caplog: LogCaptureFixture) -> None:
    """Ensure that when the report is not base64 an error is logged."""
    mock_post = RequestMockerTest.mock_requests_post(mocker, {
        'data': {
            'status': 'Success: {0}'.format(HTTPStatus.OK),
            'base64EncodedReport': 'not-base64',
        },
    })

    base64_report = reports_service.generate_questionnaire_report(
        QUESTIONNAIRE_REPORT_REQUEST_DATA,
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report is None

    assert caplog.records[0].message == 'The generated questionnaire PDF report is not in the base64 format.'
    assert caplog.records[0].levelname == 'ERROR'
