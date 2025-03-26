from django.contrib.auth.models import Group

import pytest
from rest_framework.authtoken.models import Token

from opal.caregivers.models import CaregiverProfile, SecurityQuestion
from opal.core.test_utils import CommandTestMixin
from opal.hospital_settings.models import Institution, Site
from opal.patients import factories
from opal.patients.models import HospitalPatient, Patient, Relationship
from opal.users.models import Caregiver, User

pytestmark = pytest.mark.django_db()


class TestInsertTestData(CommandTestMixin):
    """Test class to group the `insert_test_data` command tests."""

    def test_insert(self) -> None:
        """Ensure that test data is inserted when there is no existing data."""
        stdout, _stderr = self._call_command('insert_test_data')

        assert Institution.objects.count() == 1
        assert Site.objects.count() == 4
        assert Patient.objects.count() == 5
        assert HospitalPatient.objects.count() == 6
        assert CaregiverProfile.objects.count() == 3
        assert Relationship.objects.count() == 7
        assert stdout == 'Test data successfully created\n'

    def test_insert_existing_data_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The insertion can be cancelled when there is already data."""
        monkeypatch.setattr('builtins.input', lambda _: 'foo')
        relationship = factories.Relationship()

        stdout, _stderr = self._call_command('insert_test_data')

        assert stdout == 'Test data insertion cancelled\n'
        relationship.refresh_from_db()

    def test_insert_existing_data_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The existing data is deleted when confirmed and new data added."""
        monkeypatch.setattr('builtins.input', lambda _: 'yes')
        relationship = factories.Relationship()
        hospital_patient = factories.HospitalPatient()

        institution = Institution.objects.get()
        site = Site.objects.get()
        patient = Patient.objects.get()
        caregiver_profile = CaregiverProfile.objects.get()
        caregiver = Caregiver.objects.get()

        stdout, _stderr = self._call_command('insert_test_data')

        assert 'Existing test data deleted' in stdout
        assert 'Test data successfully created' in stdout

        # old data was deleted
        assert not Relationship.objects.filter(pk=relationship.pk).exists()
        assert not HospitalPatient.objects.filter(pk=hospital_patient.pk).exists()
        assert not Institution.objects.filter(pk=institution.pk).exists()
        assert not Site.objects.filter(pk=site.pk).exists()
        assert not Patient.objects.filter(pk=patient.pk).exists()
        assert not CaregiverProfile.objects.filter(pk=caregiver_profile.pk).exists()
        assert not Caregiver.objects.filter(pk=caregiver.pk).exists()

        # new data was created
        assert Institution.objects.count() == 1
        assert Site.objects.count() == 4
        assert Patient.objects.count() == 5
        assert HospitalPatient.objects.count() == 6
        assert CaregiverProfile.objects.count() == 3
        assert Relationship.objects.count() == 7


class TestInitializeData(CommandTestMixin):
    """Test class to group the `initialize_data` command tests."""

    def test_insert(self) -> None:
        """Ensure that initial data is inserted when there is no existing data."""
        stdout, _stderr = self._call_command('initialize_data')

        assert Group.objects.count() == 4
        assert User.objects.count() == 2
        assert Token.objects.count() == 2
        assert SecurityQuestion.objects.count() == 6

        listener_token = Token.objects.all()[0]
        interface_engine_token = Token.objects.all()[1]

        assert 'Data successfully created\n' in stdout
        assert f'Listener token: {listener_token.key}' in stdout
        assert f'Interface Engine token: {interface_engine_token.key}' in stdout

    def test_insert_existing_data_group(self) -> None:
        """An error is shown if a group already exists."""
        Group.objects.create(name='Clinicians')
        User.objects.create(username='Listener')

        stdout, stderr = self._call_command('initialize_data')

        assert stdout == ''
        assert stderr == 'There already exists data\n'

    def test_insert_existing_data_security_questions(self) -> None:
        """An error is shown if a security questions already exists."""
        SecurityQuestion.objects.create(title='test')

        stdout, stderr = self._call_command('initialize_data')

        assert stdout == ''
        assert stderr == 'There already exists data\n'
