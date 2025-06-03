# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import secrets
from datetime import date, datetime

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandError
from django.utils import timezone

import pytest
from pytest_django.asserts import assertRaisesMessage
from pytest_mock import MockerFixture
from rest_framework.authtoken.models import Token

from opal.caregivers import factories as caregiver_factories
from opal.caregivers.models import CaregiverProfile, SecurityAnswer, SecurityQuestion
from opal.core import constants
from opal.core.test_utils import CommandTestMixin
from opal.hospital_settings.models import Institution, Site
from opal.legacy import models as legacy_models
from opal.patients import factories
from opal.patients.models import HospitalPatient, Patient, Relationship, RelationshipType, RoleType
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
        stdout, _stderr = self._call_command('insert_test_data', 'OMI')

        assert Institution.objects.count() == 1
        assert Institution.objects.get().acronym == 'OMI'
        assert Site.objects.count() == 1
        assert Patient.objects.count() == 10
        assert HospitalPatient.objects.count() == 10
        assert CaregiverProfile.objects.count() == 8
        assert RelationshipType.objects.count() == 5
        assert RelationshipType.objects.filter(role_type=RoleType.CAREGIVER).count() == 1
        assert Relationship.objects.count() == 13
        assert SecurityAnswer.objects.count() == 24
        assert GeneralTest.objects.count() == 8
        assert PathologyObservation.objects.count() == 8
        assert Note.objects.count() == 8
        assert stdout == 'Test data successfully created\n'

    def test_insert_ohigph(self) -> None:
        """Ensure that test data for the Opal Pediatric Institute is inserted when there is no existing data."""
        stdout, _stderr = self._call_command('insert_test_data', 'OHIGPH')

        assert Institution.objects.count() == 1
        assert Institution.objects.get().acronym == 'OHIGPH'
        assert Site.objects.count() == 1
        assert Patient.objects.count() == 2
        assert HospitalPatient.objects.count() == 2
        assert CaregiverProfile.objects.count() == 2
        assert RelationshipType.objects.count() == 5
        assert RelationshipType.objects.filter(role_type=RoleType.CAREGIVER).count() == 1
        assert Relationship.objects.count() == 3
        assert SecurityAnswer.objects.count() == 6
        assert GeneralTest.objects.count() == 0
        assert PathologyObservation.objects.count() == 0
        assert Note.objects.count() == 0
        assert stdout == 'Test data successfully created\n'

    def test_insert_existing_data_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The insertion can be cancelled when there is already data."""
        monkeypatch.setattr('builtins.input', lambda _: 'foo')
        relationship = factories.Relationship.create()

        stdout, _stderr = self._call_command('insert_test_data', 'OMI')

        assert stdout == 'Test data insertion cancelled\n'
        relationship.refresh_from_db()

    def test_insert_existing_data_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The existing data is deleted when confirmed and new data added."""
        monkeypatch.setattr('builtins.input', lambda _: 'yes')
        relationship_type = factories.RelationshipType.create(name='Family', role_type=RoleType.CAREGIVER)
        relationship = factories.Relationship.create(type=relationship_type)
        hospital_patient = factories.HospitalPatient.create()
        security_answer = caregiver_factories.SecurityAnswer.create(user=relationship.caregiver)

        institution = Institution.objects.get()
        site = Site.objects.get()
        patient = Patient.objects.get()
        caregiver_profile = CaregiverProfile.objects.get()
        caregiver = Caregiver.objects.get()

        stdout, _stderr = self._call_command('insert_test_data', 'OMI')

        assert 'Existing test data deleted' in stdout
        assert 'Test data successfully created' in stdout

        # old data was deleted
        assert not RelationshipType.objects.filter(pk=relationship_type.pk).exists()
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
        assert Site.objects.count() == 1
        assert Patient.objects.count() == 10
        assert HospitalPatient.objects.count() == 10
        assert CaregiverProfile.objects.count() == 8
        assert Relationship.objects.count() == 13
        assert RelationshipType.objects.count() == 5
        assert SecurityAnswer.objects.count() == 24

    def test_insert_existing_data_force_delete(self) -> None:
        """The existing data is deleted without confirmation."""
        relationship = factories.Relationship.create()
        factories.HospitalPatient.create()
        caregiver_factories.SecurityAnswer.create(user=relationship.caregiver)

        stdout, _stderr = self._call_command('insert_test_data', 'OMI', '--force-delete')

        assert 'Existing test data deleted' in stdout
        assert 'Test data successfully created' in stdout

    def test_create_security_answers(self) -> None:
        """Ensure that the security answer's question depends on the user's language."""
        self._call_command('insert_test_data', 'OMI')

        caregiver_en = CaregiverProfile.objects.get(user__first_name='Marge')
        question_en = SecurityAnswer.objects.filter(user=caregiver_en)[0].question
        caregiver_fr = CaregiverProfile.objects.filter(user__language='fr').first()

        assert question_en == 'What is the name of your first pet?'
        # left to catch any changes to the languages
        # if changed, assert that the French caregiver has a French security question
        assert caregiver_fr is None

    def test_birth_date_calculation_before(self, mocker: MockerFixture) -> None:
        """Ensure that the birth date is calculated correctly when the current date is before the birth date."""
        # set today before Bart's birth day in the year (Feb 22nd)
        now = datetime(2024, 1, 18, tzinfo=timezone.get_current_timezone())
        mocker.patch.object(timezone, 'now', return_value=now)

        self._call_command('insert_test_data', 'OMI')

        bart = Patient.objects.get(first_name='Bart')
        assert bart.date_of_birth == date(2009, 2, 23)

    def test_birth_date_calculation_after(self, mocker: MockerFixture) -> None:
        """Ensure that the birth date is calculated correctly when the current date is after the birth date."""
        # set today after Bart's birth day in the year (Feb 22nd)
        now = datetime(2024, 2, 23, tzinfo=timezone.get_current_timezone())
        mocker.patch.object(timezone, 'now', return_value=now)

        self._call_command('insert_test_data', 'OMI')

        bart = Patient.objects.get(first_name='Bart')
        assert bart.date_of_birth == date(2010, 2, 23)


@pytest.mark.django_db(databases=['default', 'legacy'])
class TestInitializeData(CommandTestMixin):
    """Test class to group the `initialize_data` command tests."""

    @pytest.fixture(autouse=True)
    def _add_legacy_role(self) -> None:
        legacy_models.LegacyOARole.objects.create(name_en='System Administrator')

    def test_insert(self) -> None:
        """Ensure that initial data is inserted when there is no existing data."""
        stdout, _stderr = self._call_command('initialize_data')

        assert Group.objects.count() == 7
        assert User.objects.count() == 6
        assert Token.objects.count() == 5
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
        orms_token = Token.objects.get(user__username='orms')

        assert 'Data successfully created\n' in stdout
        assert f'listener token: {listener_token.key}' in stdout
        assert f'listener-registration token: {registration_listener_token.key}' in stdout
        assert f'interface-engine token: {interface_engine_token.key}' in stdout
        assert f'opaladmin-backend-legacy token: {legacy_backend_token.key}' in stdout
        assert f'orms token: {orms_token.key}' in stdout

    @pytest.mark.usefixtures('set_orms_disabled')
    def test_insert_orms_disabled(self) -> None:
        """Ensure that orms specific data is not inserted if ORMS disabled."""
        stdout, _stderr = self._call_command('initialize_data')

        assert Group.objects.count() == 6
        assert User.objects.count() == 5
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
        assert f'opaladmin-backend-legacy token: {legacy_backend_token.key}' in stdout

    def test_insert_tokens(self) -> None:
        """Ensure that initial data is inserted with existing system users and their existing tokens are returned."""
        listener = User.objects.create(username='listener')
        registration_listener = User.objects.create(username='listener-registration')
        interface_engine = User.objects.create(username='interface-engine')
        legacy_backend = User.objects.create(username='opaladmin-backend-legacy')
        orms = User.objects.create(username='orms')

        token_listener = Token.objects.create(user=listener)
        token_registration_listener = Token.objects.create(user=registration_listener)
        token_interface_engine = Token.objects.create(user=interface_engine)
        token_legacy_backend = Token.objects.create(user=legacy_backend)
        token_orms = Token.objects.create(user=orms)

        stdout, _stderr = self._call_command('initialize_data')

        assert Token.objects.count() == 5

        listener_token = Token.objects.get(user__username='listener')
        registration_listener_token = Token.objects.get(user__username='listener-registration')
        interface_engine_token = Token.objects.get(user__username='interface-engine')
        legacy_backend_token = Token.objects.get(user__username='opaladmin-backend-legacy')
        orms_token = Token.objects.get(user__username='orms')

        assert 'Data successfully created\n' in stdout
        assert token_listener == listener_token
        assert token_registration_listener == registration_listener_token
        assert token_interface_engine == interface_engine_token
        assert token_legacy_backend == legacy_backend_token
        assert token_orms == orms_token

        assert f'listener token: {listener_token.key}' in stdout
        assert f'listener-registration token: {registration_listener_token.key}' in stdout
        assert f'interface-engine token: {interface_engine_token.key}' in stdout
        assert f'opaladmin-backend-legacy token: {legacy_backend_token.key}' in stdout
        assert f'orms token: {orms_token.key}' in stdout

    @pytest.mark.usefixtures('set_orms_disabled')
    def test_insert_tokens_orms_disabled(self) -> None:
        """Ensure that initial data is inserted except orms data if ORMS disabled."""
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
        assert f'opaladmin-backend-legacy token: {legacy_backend_token.key}' in stdout

        message = 'Token matching query does not exist.'
        with assertRaisesMessage(ObjectDoesNotExist, message):
            Token.objects.get(user__username='orms')

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
        stdout, _stderr = self._call_command('initialize_data')

        listener = User.objects.get(username='listener')
        registration_listener = User.objects.get(username='listener-registration')
        interface_engine = User.objects.get(username='interface-engine')
        legacy_backend = User.objects.get(username='opaladmin-backend-legacy')
        orms = User.objects.get(username='orms')

        token_listener = Token.objects.get(user=listener)
        token_registration_listener = Token.objects.get(user=registration_listener)
        token_interface_engine = Token.objects.get(user=interface_engine)
        token_legacy_backend = Token.objects.get(user=legacy_backend)
        token_orms = Token.objects.get(user=orms)

        stdout, _stderr = self._call_command('initialize_data', '--force-delete')

        assert Group.objects.count() == 7
        assert User.objects.count() == 6
        assert Token.objects.count() == 5
        assert SecurityQuestion.objects.count() == 6

        assert 'Deleting existing data\n' in stdout
        assert 'Data successfully deleted\n' in stdout
        assert 'Data successfully created\n' in stdout

        token_listener.refresh_from_db()
        token_registration_listener.refresh_from_db()
        token_interface_engine.refresh_from_db()
        token_legacy_backend.refresh_from_db()
        token_orms.refresh_from_db()

    @pytest.mark.usefixtures('set_orms_disabled')
    def test_insert_existing_data_force_delete_orms_disabled(self) -> None:
        """Existing data with the exception of system users is deleted before inserted and skips ORMS data."""
        stdout, _stderr = self._call_command('initialize_data')

        listener = User.objects.get(username='listener')
        registration_listener = User.objects.get(username='listener-registration')
        interface_engine = User.objects.get(username='interface-engine')
        legacy_backend = User.objects.get(username='opaladmin-backend-legacy')

        token_listener = Token.objects.get(user=listener)
        token_registration_listener = Token.objects.get(user=registration_listener)
        token_interface_engine = Token.objects.get(user=interface_engine)
        token_legacy_backend = Token.objects.get(user=legacy_backend)

        stdout, _stderr = self._call_command('initialize_data', '--force-delete')

        assert Group.objects.count() == 6
        assert User.objects.count() == 5
        assert Token.objects.count() == 4
        assert SecurityQuestion.objects.count() == 6

        assert 'Deleting existing data\n' in stdout
        assert 'Data successfully deleted\n' in stdout
        assert 'Data successfully created\n' in stdout

        message = 'User matching query does not exist.'
        with assertRaisesMessage(ObjectDoesNotExist, message):
            User.objects.get(username='orms')

        token_listener.refresh_from_db()
        token_registration_listener.refresh_from_db()
        token_interface_engine.refresh_from_db()
        token_legacy_backend.refresh_from_db()

    def test_delete_clinicalstaff_only(self) -> None:
        """Only existing clinical staff users are deleted, not caregivers."""
        # create a group to trigger the existing data check
        Group.objects.create(name='Clinicians')
        User.objects.create(username='johnwayne')
        # a caregiver that should not be deleted by the command
        caregiver = caregiver_factories.CaregiverProfile.create()

        stdout, _stderr = self._call_command('initialize_data', '--force-delete')

        # ensure that the caregiver is not deleted but the user was
        caregiver.refresh_from_db()
        assert Caregiver.objects.count() == 1
        assert not User.objects.filter(username='johnwayne').exists()
        assert 'Deleting existing data\n' in stdout
        assert 'Data successfully deleted\n' in stdout
        assert 'Data successfully created\n' in stdout

    @pytest.mark.parametrize(
        'arg_name',
        [
            '--listener-token',
            '--listener-registration-token',
            '--interface-engine-token',
            '--opaladmin-backend-legacy-token',
        ],
    )
    def test_insert_existing_data_predefined_tokens_invalid(self, arg_name: str) -> None:
        """Tokens for system users can be provided."""
        token = secrets.token_hex(19)

        with pytest.raises(CommandError, match=f"{arg_name}: invalid token value: '{token}'"):
            self._call_command('initialize_data', f'{arg_name}={token}')

        token = secrets.token_hex(21)

        with pytest.raises(CommandError, match=f"{arg_name}: invalid token value: '{token}'"):
            self._call_command('initialize_data', f'{arg_name}={token}')

    @pytest.mark.parametrize(
        'username',
        [
            'listener',
            'listener-registration',
            'interface-engine',
            'opaladmin-backend-legacy',
        ],
    )
    def test_insert_existing_data_predefined_tokens(self, username: str) -> None:
        """Tokens for system users can be provided."""
        random_token = secrets.token_hex(20)

        self._call_command('initialize_data', f'--{username}-token={random_token}')

        user = User.objects.get(username=username)
        token = Token.objects.get(user=user)

        assert token.key == random_token

    def test_insert_superuser_random_password(self) -> None:
        """An admin user with a random password us generated."""
        stdout, _stderr = self._call_command('initialize_data')

        user = User.objects.get(username='admin')

        assert user.is_staff
        assert user.is_superuser
        assert user.has_usable_password()

        legacy_models.LegacyOAUser.objects.get(username='admin')

        assert 'Created superuser with username "admin"' in stdout
        assert 'and generated password: ' in stdout

    def test_insert_superuser_predefined_password(self) -> None:
        """A predefined password can be provided for the admin user."""
        random_password = secrets.token_urlsafe(constants.ADMIN_PASSWORD_MIN_LENGTH_BYTES)

        stdout, _stderr = self._call_command('initialize_data', f'--admin-password={random_password}')

        user = User.objects.get(username='admin')

        assert user.is_staff
        assert user.is_superuser
        assert user.has_usable_password()
        assert user.check_password(random_password)

        legacy_models.LegacyOAUser.objects.get(username='admin')

        assert 'Created superuser with username "admin"' in stdout
        assert 'and generated password' not in stdout

    def test_insert_superuser_predefined_password_invalid(self) -> None:
        """The password for the admin user needs to have a minimum length."""
        random_password = secrets.token_urlsafe(constants.ADMIN_PASSWORD_MIN_LENGTH_BYTES - 1)

        with pytest.raises(
            CommandError,
            match=f"Error: argument --admin-password: invalid password value: '{random_password}'",
        ):
            self._call_command('initialize_data', f'--admin-password={random_password}')
