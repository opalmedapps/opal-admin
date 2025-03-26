"""Test module for common validators of specific fields throughout opal system"""

from django.core.exceptions import ValidationError

from pytest_django.asserts import assertRaisesMessage

from ..validators import ramq_validator


def test_ramq_validator_raise_exception_fail_shorter_than_accepted() -> None:
    """Ensure that exception is caught for wrong format `shorter than supposed to be`"""

    expected_message = ramq_validator.message
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        assert ramq_validator("AAAA")


def test_ramq_validator_raise_exception_fail_wrong_format() -> None:
    """Ensure that exception error for wrong format `combination letters and digits`"""

    expected_message = ramq_validator.message
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        assert ramq_validator("AAAA1234434A")


def test_ramq_validator_raise_exception_fail_starts_digits() -> None:
    """Ensure that exception error for wrong format `start with digits` """

    expected_message = ramq_validator.message
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        assert ramq_validator("12345678AAAA")


def test_ramq_validator_raise_exception_longer_than_accepted() -> None:
    """Ensure that exception error for wrong format `start with digits` """

    expected_message = ramq_validator.message
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        assert ramq_validator("12345678AAAA")


def test_ramq_validator_pass_case() -> None:
    """Ensure that exception is not thrown in the correct case"""

    assert ramq_validator("AAAA12345678") is None
