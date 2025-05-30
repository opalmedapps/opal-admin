# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test module for common validators of specific fields throughout opal system."""

from django.core.exceptions import ValidationError

from pytest_django.asserts import assertRaisesMessage

from ..validators import validate_ramq


def test_ramq_validator_fail_short_than_accepted() -> None:
    """Ensure that exception is caught for wrong format `shorter than supposed to be`."""
    expected_message = str(validate_ramq.message)
    with assertRaisesMessage(ValidationError, expected_message):
        validate_ramq('AAAA')


def test_ramq_validator_fail_wrong_format() -> None:
    """Ensure that exception is caught for wrong format `combination letters and digits`."""
    expected_message = str(validate_ramq.message)
    with assertRaisesMessage(ValidationError, expected_message):
        validate_ramq('AAAA1234434A')


def test_ramq_validator_fail_starts_digits() -> None:
    """Ensure that exception is caught for wrong format `start with digits`."""
    expected_message = str(validate_ramq.message)
    with assertRaisesMessage(ValidationError, expected_message):
        validate_ramq('12345678AAAA')


def test_ramq_validator_fail_longer_than_accepted() -> None:
    """Ensure that exception is caught for wrong format `longer than supposed`."""
    expected_message = str(validate_ramq.message)
    with assertRaisesMessage(ValidationError, expected_message):
        validate_ramq('AAAA12345678AAAA')


def test_ramq_validator_fail_lowercase() -> None:
    """Ensure that exception is caught for wrong format `use of lowercase`."""
    expected_message = str(validate_ramq.message)
    with assertRaisesMessage(ValidationError, expected_message):
        validate_ramq('aaaa12345678')


def test_ramq_validator_pass_case() -> None:
    """Ensure correct case passes successfully."""
    validate_ramq('AAAA12345678')
