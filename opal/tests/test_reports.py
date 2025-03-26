import base64

from ..services.reports import QuestionnaireReportService

reports_service = QuestionnaireReportService()


def test_is_base64_valid_string_returns_true() -> None:
    """Ensure `True` value is returned for a valid base64 string."""
    base64_bytes = base64.b64encode(b'TEST')
    base64_message = base64_bytes.decode('ascii')
    assert reports_service._is_base64(base64_message) is True


def test_is_base64_invalid_string_returns_false() -> None:
    """Ensure `False` value is returned for an invalid base64 string."""
    assert reports_service._is_base64('TEST1') is False
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
