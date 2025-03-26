from django.contrib.auth.models import Group
from django.core.management.base import CommandError

import pytest
from rest_framework.authtoken.models import Token

from opal.caregivers import factories as caregiver_factories
from opal.caregivers.models import CaregiverProfile, SecurityAnswer, SecurityQuestion
from opal.core.test_utils import CommandTestMixin
from opal.hospital_settings.models import Institution, Site
from opal.patients import factories
from opal.patients.models import HospitalPatient, Patient, Relationship
from opal.test_results.models import GeneralTest, Note, PathologyObservation
from opal.users.models import Caregiver, User

pytestmark = pytest.mark.django_db()


class TestInsertTestData(CommandTestMixin):
    """Test class to group the `insert_test_data` command tests."""

    def test_insert_missing_institution(self) -> None:
        """Ensure that the institution argument is required and validated against the institution options."""
        with pytest.raises(CommandError, match='the following arguments are required: institution'):
            self._call_command('insert_test_data')

        with pytest.raises(CommandError, match="argument institution: invalid InstitutionOption value: 'muhc'"):
            self._call_command('insert_test_data', 'muhc')

    def test_insert(self) -> None:
        """Ensure that test data is inserted when there is no existing data."""
        stdout, _stderr = self._call_command('insert_test_data', 'MUHC')

        assert Institution.objects.count() == 1
        assert Institution.objects.get().acronym == 'MUHC'
        assert Site.objects.count() == 5
        assert Patient.objects.count() == 7
        assert HospitalPatient.objects.count() == 8
        assert CaregiverProfile.objects.count() == 5
        assert Relationship.objects.count() == 11
        assert SecurityAnswer.objects.count() == 12
        assert GeneralTest.objects.count() == 5
        assert PathologyObservation.objects.count() == 5
        assert Note.objects.count() == 5
        assert stdout == 'Test data successfully created\n'

    def test_insert_chusj(self) -> None:
        """Ensure that test data for Sainte-Justine is inserted when there is no existing data."""
        stdout, _stderr = self._call_command('insert_test_data', 'CHUSJ')

        assert Institution.objects.count() == 1
        assert Institution.objects.get().acronym == 'CHUSJ'
        assert Site.objects.count() == 1
        assert Patient.objects.count() == 2
        assert HospitalPatient.objects.count() == 2
        assert CaregiverProfile.objects.count() == 3
        assert Relationship.objects.count() == 3
        assert SecurityAnswer.objects.count() == 6
        assert GeneralTest.objects.count() == 0
        assert PathologyObservation.objects.count() == 0
        assert Note.objects.count() == 0
        assert stdout == 'Test data successfully created\n'

    def test_insert_existing_data_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The insertion can be cancelled when there is already data."""
        monkeypatch.setattr('builtins.input', lambda _: 'foo')
        relationship = factories.Relationship()

        stdout, _stderr = self._call_command('insert_test_data', 'MUHC')

        assert stdout == 'Test data insertion cancelled\n'
        relationship.refresh_from_db()

    def test_insert_existing_data_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The existing data is deleted when confirmed and new data added."""
        monkeypatch.setattr('builtins.input', lambda _: 'yes')
        relationship = factories.Relationship()
        hospital_patient = factories.HospitalPatient()
        security_answer = caregiver_factories.SecurityAnswer(user=relationship.caregiver)

        institution = Institution.objects.get()
        site = Site.objects.get()
        patient = Patient.objects.get()
        caregiver_profile = CaregiverProfile.objects.get()
        caregiver = Caregiver.objects.get()

        stdout, _stderr = self._call_command('insert_test_data', 'MUHC')

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
        assert not SecurityAnswer.objects.filter(pk=security_answer.pk).exists()

        # new data was created
        assert Institution.objects.count() == 1
        assert Site.objects.count() == 5
        assert Patient.objects.count() == 7
        assert HospitalPatient.objects.count() == 8
        assert CaregiverProfile.objects.count() == 5
        assert Relationship.objects.count() == 11
        assert SecurityAnswer.objects.count() == 12

    def test_insert_existing_data_force_delete(self) -> None:
        """The existing data is deleted without confirmation."""
        relationship = factories.Relationship()
        factories.HospitalPatient()
        caregiver_factories.SecurityAnswer(user=relationship.caregiver)

        stdout, _stderr = self._call_command('insert_test_data', 'MUHC', '--force-delete')

        assert 'Existing test data deleted' in stdout
        assert 'Test data successfully created' in stdout

    def test_create_security_answers(self) -> None:
        """Ensure that the security answer's question depends on the user's language."""
        self._call_command('insert_test_data', 'MUHC')

        caregiver_en = CaregiverProfile.objects.get(user__first_name='Marge')
        question_en = SecurityAnswer.objects.filter(user=caregiver_en)[0].question
        caregiver_fr = CaregiverProfile.objects.filter(user__language='fr').first()

        assert question_en == 'What is the name of your first pet?'
        # left to catch any changes to the languages
        # if changed, assert that the French caregiver has a French security question
        assert caregiver_fr is None


class TestInitializeData(CommandTestMixin):
    """Test class to group the `initialize_data` command tests."""

    def test_insert(self) -> None:
        """Ensure that initial data is inserted when there is no existing data."""
        stdout, _stderr = self._call_command('initialize_data')

        assert Group.objects.count() == 7
        assert User.objects.count() == 4
        assert Token.objects.count() == 4
        assert SecurityQuestion.objects.count() == 6

        for group in Group.objects.all():
            group.full_clean()
        for user in User.objects.all():
            user.full_clean()
        for token in Token.objects.all():
            token.full_clean()
        for security_question in SecurityQuestion.objects.all():
            security_question.full_clean()

        listener_token = Token.objects.get(user__username='listener')
        registration_listener_token = Token.objects.get(user__username='listener-registration')
        interface_engine_token = Token.objects.get(user__username='interface-engine')
        legacy_backend_token = Token.objects.get(user__username='opaladmin-backend-legacy')

        assert 'Data successfully created\n' in stdout
        assert f'listener token: {listener_token.key}' in stdout
        assert f'listener-registration token: {registration_listener_token.key}' in stdout
        assert f'interface-engine token: {interface_engine_token.key}' in stdout
        assert f'opaladmin-backend-legacy token: {legacy_backend_token}' in stdout

    def test_insert_tokens(self) -> None:
        """Ensure that initial data is inserted with existing system users and their existing tokens are returned."""
        listener = User.objects.create(username='listener')
        registration_listener = User.objects.create(username='listener-registration')
        interface_engine = User.objects.create(username='interface-engine')
        legacy_backend = User.objects.create(username='opaladmin-backend-legacy')

        token_listener = Token.objects.create(user=listener)
        token_registration_listener = Token.objects.create(user=registration_listener)
        token_interface_engine = Token.objects.create(user=interface_engine)
        token_legacy_backend = Token.objects.create(user=legacy_backend)

        stdout, _stderr = self._call_command('initialize_data')

        assert Token.objects.count() == 4

        listener_token = Token.objects.get(user__username='listener')
        registration_listener_token = Token.objects.get(user__username='listener-registration')
        interface_engine_token = Token.objects.get(user__username='interface-engine')
        legacy_backend_token = Token.objects.get(user__username='opaladmin-backend-legacy')

        assert 'Data successfully created\n' in stdout
        assert token_listener == listener_token
        assert token_registration_listener == registration_listener_token
        assert token_interface_engine == interface_engine_token
        assert token_legacy_backend == legacy_backend_token
        assert f'listener token: {listener_token.key}' in stdout
        assert f'listener-registration token: {registration_listener_token.key}' in stdout
        assert f'interface-engine token: {interface_engine_token.key}' in stdout
        assert f'opaladmin-backend-legacy token: {legacy_backend_token}' in stdout

    def test_insert_muhc_deployment(self) -> None:
        """Ensure that initial data is inserted and includes sites and muhc institution given flag."""
        stdout, _stderr = self._call_command('initialize_data', '--muhc-deployment')

        assert Group.objects.count() == 7
        assert User.objects.count() == 4
        assert Token.objects.count() == 4
        assert SecurityQuestion.objects.count() == 6
        assert Institution.objects.count() == 1
        assert Site.objects.count() == 5

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

    def test_insert_existing_data_force_delete(self) -> None:
        """Existing data with the exception of system users is deleted before inserted."""
        stdout, stderr = self._call_command('initialize_data')

        listener = User.objects.get(username='listener')
        registration_listener = User.objects.get(username='listener-registration')
        interface_engine = User.objects.get(username='interface-engine')
        legacy_backend = User.objects.get(username='opaladmin-backend-legacy')

        token_listener = Token.objects.get(user=listener)
        token_registration_listener = Token.objects.get(user=registration_listener)
        token_interface_engine = Token.objects.get(user=interface_engine)
        token_legacy_backend = Token.objects.get(user=legacy_backend)

        stdout, stderr = self._call_command('initialize_data', '--force-delete')

        assert Group.objects.count() == 7
        assert User.objects.count() == 4
        assert Token.objects.count() == 4
        assert SecurityQuestion.objects.count() == 6

        assert 'Deleting existing data\n' in stdout
        assert 'Data successfully deleted\n' in stdout
        assert 'Data successfully created\n' in stdout

        token_listener.refresh_from_db()
        token_registration_listener.refresh_from_db()
        token_interface_engine.refresh_from_db()
        token_legacy_backend.refresh_from_db()
