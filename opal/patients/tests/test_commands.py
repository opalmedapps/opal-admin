from datetime import date
from unittest.mock import patch

import pytest
from pytest_mock.plugin import MockerFixture

from opal.patients import factories as patient_factories
from opal.patients.models import Patient, Relationship, RelationshipStatus
from opal.utils.tests.test_commands import CommandTestMixin

pytestmark = pytest.mark.django_db(databases=['default'])


original = Patient.calculate_age


class TestExpireRelationshipsCommand(CommandTestMixin):
    """TODO"""

    TODAY_FAKE_DATE = date(2014, 1, 15)

    # @pytest.fixture(autouse=True)
    # def _before_all(self, mocker: MockerFixture) -> None:
    #     """Mock today's date before the following tests, to ensure results don't vary based on the current date"""
    #     mocker.patch.object(date, 'today', return_value=self.TODAY_FAKE_DATE)

    def fixed_date(date_of_birth: date):
        return original(date_of_birth=date_of_birth, reference_date=date(2014, 1, 15))

    # def test_not_expired(self):
    #
    # def test_expired(self):
    #
    # def test_empty_date_of_birth(self):
    #
    # def test_birthday_yesterday(self):

    @patch.object(Patient, 'calculate_age', side_effect=fixed_date)
    def test_birthday_today(self, mocker: MockerFixture):
        relationship = patient_factories.Relationship(
            patient=patient_factories.Patient(date_of_birth=date(2000, 1, 15)),
            type=patient_factories.RelationshipType(end_age=14),
            status=RelationshipStatus.CONFIRMED,
        )
        message, error = self._call_command('expire_relationships')
        print(message)
        res = relationship.refresh_from_db()
        print('RESULT', res)
        assert relationship.status is RelationshipStatus.EXPIRED.value


    # def test_birthday_tomorrow(self):
