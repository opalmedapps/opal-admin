from datetime import date
from unittest.mock import patch

import pytest
from pytest_mock.plugin import MockerFixture

from opal.patients import factories as patient_factories
from opal.patients.models import Patient, RelationshipStatus
from opal.utils.tests.test_commands import CommandTestMixin

pytestmark = pytest.mark.django_db(databases=['default'])


calculate_age_original = Patient.calculate_age


def calculate_age_fixed_date(date_of_birth: date):
    """Mock today's date (reference date) before each test, to ensure results don't vary based on the current date"""
    return calculate_age_original(date_of_birth=date_of_birth, reference_date=date(2014, 1, 15))


class TestExpireRelationshipsCommand(CommandTestMixin):
    """TODO"""

    def test_not_expired(self):

    def test_expired(self):


    @patch.object(Patient, 'calculate_age', side_effect=calculate_age_fixed_date)
    def test_birthday_yesterday(self, mocker: MockerFixture):
        relationship = self.create_relationship(date(2000, 1, 14))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED.value

    @patch.object(Patient, 'calculate_age', side_effect=calculate_age_fixed_date)
    def test_birthday_today(self, mocker: MockerFixture):
        relationship = self.create_relationship(date(2000, 1, 15))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED.value

    @patch.object(Patient, 'calculate_age', side_effect=calculate_age_fixed_date)
    def test_birthday_tomorrow(self, mocker: MockerFixture):
        relationship = self.create_relationship(date(2000, 1, 16))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED.value

    def create_relationship(self, patient_date_of_birth):
        return patient_factories.Relationship(
            patient=patient_factories.Patient(date_of_birth=patient_date_of_birth),
            type=patient_factories.RelationshipType(end_age=14),
            status=RelationshipStatus.CONFIRMED,
        )
