import base64
import json
from http import HTTPStatus
from pathlib import Path
from unittest.mock import MagicMock

from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from requests import Response
from requests.exceptions import RequestException

from ..services.reports import ReportService

ENCODING = 'utf-8'

reports_service = ReportService()


def _create_generated_report_data(status: str) -> dict[str, dict[str, str]]:
    return {
        'data': {
            'status': 'Success: {0}'.format(status),
            'base64EncodedReport': 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG',
        },
    }


def _mock_requests_post(
    mocker: MockerFixture,
    generated_report_data: dict[str, dict[str, str]],
) -> MagicMock:
    # mock actual web API call
    mock_post = mocker.patch('requests.post')
    response = Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(generated_report_data).encode(ENCODING)
    mock_post.return_value = response

    return mock_post


# _is_base64

def test_is_base64_valid_string_returns_true() -> None:
    """Ensure `True` value is returned for a valid base64 string."""
    base64_bytes = base64.b64encode(b'TEST')
    base64_message = base64_bytes.decode('ascii')
    assert reports_service._is_base64(base64_message) is True


def test_is_base64_invalid_string_returns_false() -> None:
    """Ensure `False` value is returned for an invalid base64 string."""
    assert reports_service._is_base64('TEST1') is False
    assert reports_service._is_base64(b'TEST1') is False
    assert reports_service._is_base64('TEST==') is False
    assert reports_service._is_base64('==') is False
    assert reports_service._is_base64('.') is False


def test_is_base64_empty_string_returns_false() -> None:
    """Ensure `False` value is returned for an empty string."""
    assert reports_service._is_base64('') is False
    assert reports_service._is_base64('\t') is False
    assert reports_service._is_base64('\n') is False
    assert reports_service._is_base64('\r') is False
    assert reports_service._is_base64('\r\n') is False


def test_is_base64_none_returns_false() -> None:
    """Ensure `False` value is returned for a passed `None` value."""
    assert reports_service._is_base64(None) is False


def test_is_base64_non_ascii_error() -> None:
    """Ensure function catches non-ascii character exceptions/errors."""
    string = ''
    try:
        string = reports_service._is_base64('Centre universitaire de santé McGill')
    except ValueError:
        assert string == ''


def test_is_base64_non_base64_error() -> None:
    """Ensure function catches non-base64 character exceptions/errors."""
    string = ''
    try:
        string = reports_service._is_base64('@opal@')
    except ValueError:
        assert string == ''


# _encode_image_to_base64

def test_encode_image_to_base64() -> None:
    """Ensure function returns encoded base64 string of the logo image."""
    base64_str = reports_service._encode_image_to_base64(Path('opal/tests/fixtures/test_logo.png'))
    assert base64_str != ''
    assert base64_str is not None
    assert reports_service._is_base64(base64_str)


def test_encode_image_to_base64_invalid_path() -> None:
    """Ensure function returns an empty string for a given invalid file path."""
    base64_str = ''
    try:
        base64_str = reports_service._encode_image_to_base64(Path('test/invalid/path'))
    except IOError:
        assert base64_str == ''

    try:
        base64_str = reports_service._encode_image_to_base64(Path(''))
    except IOError:
        assert base64_str == ''


def test_encode_image_to_base64_not_image() -> None:
    """Ensure function returns an empty string for a given non-image file."""
    base64_str = ''
    try:
        base64_str = reports_service._encode_image_to_base64(
            Path('opal/tests/fixtures/non_image_file.txt'),
        )
    except IOError:
        assert base64_str == ''


# _request_base64_report

def test_request_base64_report(mocker: MockerFixture) -> None:
    """Ensure successful report request returns base64 encoded pdf report."""
    generated_report_data = _create_generated_report_data(str(HTTPStatus.OK))
    mock_post = _mock_requests_post(mocker, generated_report_data)

    response_base64_report = reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert response_base64_report == 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'

    mock_post.assert_called_once()
    post_data = json.loads(mock_post.call_args[1]['data'])

    assert list(post_data.keys()) == ['patient_id', 'logo_base64', 'language']


def test_request_base64_report_error(mocker: MockerFixture) -> None:
    """Ensure request failure is handled and does not result in error."""
    # mock actual web API call to raise a request error
    generated_report_data = _create_generated_report_data(str(HTTPStatus.OK))
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.side_effect = RequestException('request failed')

    base64_report = reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report == ''


def test_request_base64_report_bad_request(mocker: MockerFixture) -> None:
    """Ensure request failure (bad request response) is handled and does not result in error."""
    # mock actual web API call to raise a request error
    generated_report_data = _create_generated_report_data(str(HTTPStatus.BAD_REQUEST))
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.BAD_REQUEST

    base64_report = reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.BAD_REQUEST
    assert base64_report == ''


def test_request_base64_report_json_key_error(mocker: MockerFixture) -> None:
    """Ensure response json key failure is handled and does not result in error."""
    generated_report_data = _create_generated_report_data(str(HTTPStatus.OK))
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value._content = json.dumps({}).encode(ENCODING)

    base64_report = reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report == ''


def test_request_base64_report_json_decode_error(mocker: MockerFixture) -> None:
    """Ensure response json decode failure is handled and does not result in error."""
    generated_report_data = _create_generated_report_data(str(HTTPStatus.OK))
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value._content = 'test string'.encode(ENCODING)

    base64_report = reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report == ''


def test_request_base64_report_is_string(mocker: MockerFixture) -> None:
    """Ensure returned base64EncodedReport value is a string."""
    generated_report_data = _create_generated_report_data(str(HTTPStatus.OK))
    mock_post = _mock_requests_post(mocker, generated_report_data)

    base64_report = reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert isinstance(base64_report, str)


def test_request_base64_report_not_string(mocker: MockerFixture) -> None:
    """Ensure returned base64EncodedReport non-string value is handled and does not result in error."""
    generated_report_data = _create_generated_report_data(str(HTTPStatus.OK))
    mock_post = _mock_requests_post(mocker, generated_report_data)
    data = _create_generated_report_data(str(HTTPStatus.OK))
    data['data']['base64EncodedReport'] = 123  # type: ignore
    mock_post.return_value._content = json.dumps(data).encode(ENCODING)

    base64_report = reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert base64_report == ''


def test_request_base64_report_uses_settings(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """Ensure base64 report request uses report settings."""
    settings.LEGACY_QUESTIONNAIRES_REPORT_URL = 'http://localhost:80/report'

    # mock actual web API call
    generated_report_data = _create_generated_report_data(str(HTTPStatus.OK))
    mock_post = _mock_requests_post(mocker, generated_report_data)
    mock_post.return_value.status_code = HTTPStatus.OK

    reports_service._request_base64_report(
        51,
        Path('opal/tests/fixtures/test_logo.png'),
        'en',
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK

    headers = {'Content-Type': 'application/json'}
    pload = json.dumps({
        'patient_id': 51,
        'logo_base64': reports_service._encode_image_to_base64(Path('opal/tests/fixtures/test_logo.png')),
        'language': 'en',
    })
    mock_post.assert_called_once_with(
        url='http://localhost:80/report',
        headers=headers,
        data=pload,
    )
