import base64
from pathlib import Path

from opal.utils.base64 import Base64Util

LOGO_PATH = Path('opal/tests/fixtures/test_logo.png')
TXT_FILE_PATH = Path('opal/tests/fixtures/test_txt.txt')
PDF_FILE_PATH = Path('opal/tests/fixtures/test_PDF.pdf')

base64_util = Base64Util()


# is_base64 function tests

def test_is_base64_valid_string_returns_true() -> None:
    """Ensure `True` value is returned for a valid base64 string."""
    base64_bytes = base64.b64encode(b'TEST')
    base64_message = base64_bytes.decode('ascii')
    assert base64_util.is_base64(base64_message) is True


def test_is_base64_invalid_string_returns_false() -> None:
    """Ensure `False` value is returned for an invalid base64 string."""
    assert base64_util.is_base64('TEST1') is False
    assert base64_util.is_base64('TEST==') is False
    assert base64_util.is_base64('==') is False
    assert base64_util.is_base64('.') is False


def test_is_base64_empty_string_returns_false() -> None:
    """Ensure `False` value is returned for an empty string."""
    assert base64_util.is_base64('') is False
    assert base64_util.is_base64('\t') is False
    assert base64_util.is_base64('\n') is False
    assert base64_util.is_base64('\r') is False
    assert base64_util.is_base64('\r\n') is False


def test_is_base64_type_error_returns_false() -> None:
    """Ensure `False` value is returned for a passed non-string value."""
    is_base64 = False
    try:
        assert base64_util.is_base64(b'OPALTEST') is False  # type: ignore
    except TypeError:
        assert is_base64 is False

    is_base64 = False
    try:
        assert base64_util.is_base64(None) is False
    except TypeError:
        assert is_base64 is False


def test_is_base64_non_ascii_error() -> None:
    """Ensure function catches non-ascii character exceptions/errors."""
    is_base64 = False
    try:
        is_base64 = base64_util.is_base64('Centre universitaire de santé McGill')
    except ValueError:
        assert is_base64 is False


def test_is_base64_non_base64_error() -> None:
    """Ensure function catches non-base64 character exceptions/errors."""
    is_base64 = False
    try:
        is_base64 = base64_util.is_base64('@opal@')
    except ValueError:
        assert is_base64 is False


# encode_image_to_base64 function tests

def test_encode_image_to_base64() -> None:
    """Ensure function returns encoded base64 string of the logo image."""
    base64_str = base64_util.encode_to_base64(LOGO_PATH)
    assert base64_str
    assert base64_util.is_base64(base64_str)


def test_encode_pdf_to_base64() -> None:
    """Ensure function returns encoded base64 string of the PDF file."""
    base64_str = base64_util.encode_to_base64(PDF_FILE_PATH)
    assert base64_str
    assert base64_util.is_base64(base64_str)


def test_encode_image_to_base64_invalid_path() -> None:
    """Ensure function returns an empty string for a given invalid file path."""
    try:
        base64_str = base64_util.encode_to_base64(Path('test/invalid/path'))
    except OSError:
        assert base64_str == ''

    try:
        base64_str = base64_util.encode_to_base64(Path(''))
    except OSError:
        assert base64_str == ''
