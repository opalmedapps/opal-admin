# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import date

import pytest
from pytest_mock import MockerFixture, MockType

from opal.core.test_utils import CommandTestMixin
from opal.patients import factories as patient_factories
from opal.patients.models import Patient, Relationship, RelationshipStatus

pytestmark = pytest.mark.django_db(databases=['default'])


calculate_age_original = Patient.calculate_age


def calculate_age_fixed_date(date_of_birth: date) -> int:
    """
    Mock today's date (reference date) before each test, to ensure results don't vary based on the current date.

    Args:
        date_of_birth: Same input parameter as for Patient.calculate_age.

    Returns:
        The result of Patient.calculate_age called with the input date_of_birth and a fixed reference date.
    """
    return calculate_age_original(date_of_birth=date_of_birth, reference_date=date(2014, 1, 15))


class TestExpireRelationshipsCommand(CommandTestMixin):
    """Test class for expire_relationships management command."""

    @pytest.fixture(autouse=True)
    def before(self, mocker: MockerFixture) -> MockType:
        """Mock `Patient.calculate_age` with a fixed date in place of `date.today()`."""
        return mocker.patch.object(Patient, 'calculate_age', side_effect=calculate_age_fixed_date)

    def test_not_expired(self) -> None:
        """Test patient born shortly before today's date (relationship is not expired)."""
        relationship = self._create_relationship(date(2010, 12, 31))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_expired(self) -> None:
        """Test patient born long before today's date (relationship is expired)."""
        relationship = self._create_relationship(date(1960, 12, 31))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_born_today(self) -> None:
        """Test patient born today (relationship is not expired)."""
        relationship = self._create_relationship(date(2014, 1, 15))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_future_birthday(self) -> None:
        """Test patient born in the future (relationship is not expired)."""
        relationship = self._create_relationship(date(2024, 1, 15))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_birthday_yesterday(self) -> None:
        """Test a patient close to the expiry age, whose birthday was yesterday (relationship has just expired)."""
        relationship = self._create_relationship(date(2000, 1, 14))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_birthday_today(self) -> None:
        """Test a patient close to the expiry age, whose birthday is today (relationship has just expired today)."""
        relationship = self._create_relationship(date(2000, 1, 15))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_birthday_tomorrow(self) -> None:
        """Test a patient close to the expiry age, whose birthday is tomorrow (relationship isn't expired just yet)."""
        relationship = self._create_relationship(date(2000, 1, 16))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_no_end_age(self) -> None:
        """Test a relationship with no end age, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), end_age=None)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_pending_unaffected(self) -> None:
        """Test a relationship with pending status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.PENDING)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.PENDING

    def test_denied_unaffected(self) -> None:
        """Test a relationship with denied status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.DENIED)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.DENIED

    def test_expired_unaffected(self) -> None:
        """Test a relationship with already expired status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.EXPIRED)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_revoked_unaffected(self) -> None:
        """Test a relationship with revoked status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.REVOKED)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.REVOKED

    def _create_relationship(
        self,
        patient_date_of_birth: date,
        end_age: int | None = 14,
        status: RelationshipStatus = RelationshipStatus.CONFIRMED,
    ) -> Relationship:
        """
        Quickly create a relationship with a patient who has a specific birthday.

        Returns:
            New Relationship with provided parameters.
        """
        return patient_factories.Relationship.create(
            patient=patient_factories.Patient.create(date_of_birth=patient_date_of_birth),
            type=patient_factories.RelationshipType.create(end_age=end_age),
            status=status,
        )
