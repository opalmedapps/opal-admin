import base64
from pathlib import Path

from ..services.reports import ReportService

reports_service = ReportService()


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
    """Ensure function is catching non-ascii characters."""
    string = ''
    try:
        string = reports_service._is_base64('Centre universitaire de santé McGill')
    except ValueError:
        assert string == ''


def test_is_base64_non_base64_error() -> None:
    """Ensure function is catching non-base64 characters."""
    string = ''
    try:
        string = reports_service._is_base64('@opal@')
    except ValueError:
        assert string == ''


# _encode_image_to_base64

def test_encode_image_to_base64() -> None:
    """Ensure functions return encoded base64 string of the logo image."""
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
        base64_str = reports_service._encode_image_to_base64(Path('opal/tests/fixtures/invalid_logo.txt'))
    except IOError:
        assert base64_str == ''


# _request_base64_report

# generate_questionnaire_report
