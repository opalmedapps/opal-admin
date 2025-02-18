# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module is used to provide configuration, fixtures, and plugins for pytest."""
from collections.abc import Callable, Generator
from datetime import datetime
from pathlib import Path

from django.apps import apps
from django.conf import LazySettings
from django.contrib.auth.models import Group, Permission
from django.db import connections
from django.db.models import Model
from django.test import Client

import pytest
from _pytest.config import Config
from _pytest.main import Session
from _pytest.python import Function, Module  # noqa: PLC2701
from pytest_django import DjangoDbBlocker
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from opal.core import constants
from opal.legacy import factories as legacy_factories
from opal.legacy.models import LegacyEducationalMaterialControl
from opal.legacy_questionnaires import factories
from opal.legacy_questionnaires.models import LegacyQuestionnaire, LegacyQuestionnairePatient
from opal.users.models import User

LEGACY_TEST_PATIENT_ID = 51
LEGACY_DICTIONARY_CONTENT_ID = 9000000


def pytest_collection_modifyitems(session: Session, config: Config, items: list[Function]) -> None:
    """
    Change the execution order of tests.

    Ensure that migration tests run last.
    This is to avoid the migrator from `django-test-migrations` to cause data migrations to be flushed.
    The exact cause of this is unknown: https://github.com/wemake-services/django-test-migrations/issues/330

    Docs: https://docs.pytest.org/en/latest/reference/reference.html#pytest.hookspec.pytest_collection_modifyitems

    Args:
        session: the pytest session
        config: the pytest configuration
        items: the items to test (test functions and test classes)

    """
    migration_tests = []
    original_items_order = []

    for item in items:
        # some test functions are wrapped within a class
        module = item.getparent(Module)

        if module and module.name == 'test_migrations.py':
            migration_tests.append(item)
        else:
            original_items_order.append(item)

    # modify items in place with migration tests moved to the end
    items[:] = original_items_order + migration_tests


@pytest.fixture(autouse=True)
def mock_now(mocker: MockerFixture) -> None:
    """
    Mock timezone.now to avoid jumping to the next day in UTC.

    This is an issue when tests run late in the day where the equivalent in UTC is on the next day.
    """
    mocker.patch('django.utils.timezone.now', side_effect=lambda: datetime.now().astimezone().replace(hour=13))


@pytest.fixture
def api_client() -> APIClient:
    """
    Fixture providing an instance of Django REST framework's `APIClient`.

    Returns:
        an instance of `APIClient`
    """
    return APIClient()


@pytest.fixture
def user_api_client(api_client: APIClient, django_user_model: User) -> APIClient:
    """
    Fixture providing an instance of `APIClient` (`rest_framework.test.API_Client`) with a logged in user.

    Args:
        api_client: the API client instance
        django_user_model: the `User` model type used in this project

    Returns:
        an instance of `APIClient` with a logged in user
    """
    user = django_user_model.objects.create(username='test_api_user')
    api_client.force_login(user=user)

    return api_client


@pytest.fixture
def admin_api_client(api_client: APIClient, admin_user: User) -> APIClient:
    """
    Fixture providing an instance of `APIClient` (`rest_framework.test.API_Client`) with a logged in admin user.

    Args:
        api_client: the API client instance
        admin_user: the admin user

    Returns:
        an instance of `APIClient` with a logged in admin user
    """
    api_client.force_login(user=admin_user)

    return api_client


# TODO: add additional fixture providing a caregiver?
@pytest.fixture(name='user')
def user_instance(django_user_model: User) -> User:
    """
    Fixture providing a user with no permissions.

    Args:
        django_user_model: the `User` model used in this project

    Returns:
        a `User` instance
    """
    user = django_user_model.objects.create(username='testuser')
    user.set_password('testpassword')
    user.save()

    return user


# TODO: add additional fixture providing a caregiver?
@pytest.fixture
def user_with_permission(user: User) -> Callable[[str], User]:
    """
    Fixture providing a user with a permission.

    The fixture returns a function that expects a permission
    to be added to the user.
    The expected format of the permissions is `app_label.codename`.
    For example, `users.view_user`.

    Args:
        user: the `user` fixture providing a user with no permissions

    Returns:
        a callable that adds a permission
    """
    def add_permission(permission_name: str) -> User:
        permission_names = [permission_name]

        permission_tuples = [permission.split('.') for permission in permission_names]

        permissions = [
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
            for app_label, codename in permission_tuples
        ]

        user.user_permissions.set(permissions)

        return user

    return add_permission


@pytest.fixture
def listener_user(django_user_model: User) -> User:
    """
    Fixture providing a `User` instance representing the listener.

    Args:
        django_user_model: the `User` model used in this project

    Returns:
        a user instance representing the listener
    """
    return django_user_model.objects.create_user(username=constants.USERNAME_LISTENER)


@pytest.fixture
def registration_listener_user(django_user_model: User) -> User:
    """
    Fixture providing a `User` instance representing the registration listener.

    Args:
        django_user_model: the `User` model used in this project

    Returns:
        a user instance representing the registration listener
    """
    return django_user_model.objects.create_user(username=constants.USERNAME_LISTENER_REGISTRATION)


@pytest.fixture
def interface_engine_user(django_user_model: User) -> User:
    """
    Fixture providing a `User` instance representing the interface engine.

    Args:
        django_user_model: the `User` model used in this project

    Returns:
        a user instance representing the interface engine
    """
    return django_user_model.objects.create_user(username=constants.USERNAME_INTERFACE_ENGINE)


@pytest.fixture
def legacy_backend_user(django_user_model: User) -> User:
    """
    Fixture providing a `User` instance representing the legacy backend user (OpalAdmin).

    Args:
        django_user_model: the `User` model used in this project

    Returns:
        a user instance representing the legacy backend user
    """
    return django_user_model.objects.create_user(username=constants.USERNAME_BACKEND_LEGACY)


@pytest.fixture
def orms_user(django_user_model: User, settings: LazySettings) -> User:
    """
    Fixture providing a `User` instance belonging to the ORMS users group.

    Args:
        django_user_model: the `User` model used in this project
        settings: the fixture providing access to the Django settings

    Returns:
        a user instance belonging to the ORMS users group
    """
    user = django_user_model.objects.create_user(
        username='orms-user',
        first_name='Or',
        last_name='Ms',
    )
    user.groups.add(Group.objects.create(name=settings.ORMS_GROUP_NAME))

    return user


@pytest.fixture
def orms_system_user(django_user_model: User) -> User:
    """
    Fixture providing a `User` instance representing the ORMS sytem.

    Args:
        django_user_model: the `User` model used in this project

    Returns:
        a user instance representing ORMS
    """
    return django_user_model.objects.create_user(username=constants.USERNAME_ORMS)


@pytest.fixture(autouse=True)
def set_orms_enabled(settings: LazySettings) -> None:
    """
    Fixture enables ORMS by default for all unit tests.

    Args:
        settings: the fixture providing access to the Django settings
    """
    settings.ORMS_ENABLED = True


@pytest.fixture
def set_orms_disabled(settings: LazySettings) -> None:
    """
    Fixture disables ORMS for the unit test.

    Args:
        settings: the fixture providing access to the Django settings
    """
    settings.ORMS_ENABLED = False


@pytest.fixture
def user_client(client: Client, user: User) -> Client:
    """
    Fixture providing an instance of [Client][django.test.Client] with a logged in user.

    Args:
        client: the Django test client instance
        user: the `User` instance

    Returns:
        an instance of `Client` with a logged in user
    """
    client.force_login(user)

    return client


def is_legacy_model(model: type[Model]) -> bool:
    """
    Determine whether the given model is a legacy model.

    Only models from the legacy app that are unmanaged are legacy models.

    Args:
        model: the model to check

    Returns:
        `True`, if it is a legacy model, `False` otherwise
    """
    return model._meta.app_label in {'legacy', 'legacy_questionnaires'} and not model._meta.managed


@pytest.fixture(scope='session', autouse=True)
def _manage_unmanaged_models() -> None:
    """
    Fixture allowing Django to create a test database for unmanaged models.

    Changes all unmanaged models to be managed.
    Note that this applies to any unmanaged model, not just the ones in this app.

    Inspired by:
        * https://www.caktusgroup.com/blog/2010/09/24/simplifying-the-testing-of-unmanaged-database-models-in-django/
        * https://stackoverflow.com/q/53289057
    """
    models = apps.get_models()

    unmanaged_models = [model for model in models if is_legacy_model(model)]

    for model in unmanaged_models:
        model._meta.managed = True


@pytest.fixture(autouse=True)
def _change_media_root(tmp_path: Path, settings: LazySettings) -> None:
    """
    Fixture changing the `MEDIA_ROOT` value of the settings.

    Args:
        tmp_path: Object to a temporary directory which is unique to each test function
        settings: All the configurations of the `opalAdmin backend` service
    """
    settings.MEDIA_ROOT = str(tmp_path.joinpath('media/'))


@pytest.fixture(scope='session', autouse=True)
def django_db_setup(
    django_db_setup: None,
    django_db_blocker: DjangoDbBlocker,
) -> Generator[None, None, None]:
    """
    Set up the QuestionnaireDB manually using an SQL file with the schema.

    Args:
        django_db_setup: pytest django's original DB setup fixture
        django_db_blocker: pytest fixture to allow database access here only

    Yields:
        None
    """
    with Path('opal/tests/sql/questionnairedb_functions.sql').open(encoding='utf-8') as handle:
        sql_content = handle.read()

    with Path('opal/tests/sql/questionnairedb_cleanup.sql').open(encoding='utf-8') as handle:
        sql_cleanup = handle.read()

    with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
        conn.execute(sql_content)

    yield

    with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
        conn.execute('SELECT COUNT(*) FROM questionnaire;')
        result = conn.fetchone()
        assert result[0] == 0
        conn.execute(sql_cleanup)


@pytest.fixture
def questionnaire_data(django_db_blocker: DjangoDbBlocker) -> Generator[None, None, None]:
    """
    Initialize the QuestionnaireDB with data.

    Data inserted includes the creation of questionnaires with related questions and dictionary entires.
    Additionally, instances of questionnaire answers:

    * Completed ESAS questionnaires for patientId 1, 2; in progress for patientId 3
    * Completed Patient Satisfaction Questionnaire for patientId 3
    * New Bowel Function Questionnaire for patientId 3
    * New Quality of Life - Head and Neck Cancer for patientId 2
    * New BREAST-Q Reconstruction Module Preoperative Scales
      and BREAST-Q Reconstruction Module Postoperative Scales for patientId 1

    Args:
        django_db_blocker: pytest fixture to allow database access here only

    Yields:
        None
    """
    with Path('opal/tests/sql/questionnairedb_data.sql').open(encoding='utf-8') as handle:
        sql_data = handle.read()

    with Path('opal/tests/sql/questionnairedb_cleanup.sql').open(encoding='utf-8') as handle:
        sql_cleanup = handle.read()

    with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
        # safety check to ensure that there is no data already
        conn.execute('SELECT COUNT(*) FROM questionnaire;')
        result = conn.fetchone()
        assert result[0] == 0
        conn.execute(sql_data)

    yield

    with django_db_blocker.unblock(), connections['questionnaire'].cursor() as conn:
        conn.execute(sql_cleanup)


@pytest.fixture
def databank_consent_questionnaire_and_response(
) -> tuple[LegacyQuestionnairePatient, LegacyQuestionnaire]:
    """
    Add a full databank consent questionnaire and simple response to test setup.

    Returns:
        The corresponding legacy patient record who is linked to this answer, and the questionnaire
    """
    # Legacy patient record
    consenting_patient = factories.LegacyQuestionnairePatientFactory(external_id=LEGACY_TEST_PATIENT_ID)
    consenting_patient.full_clean()
    # Questionnaire content, content ids must be non overlapping with existing test_QuestionnaireDB SQL
    middle_name_content = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID,
        content='Middle name',
        language_id=2,
    )
    middle_name_content.full_clean()
    middle_name_question = factories.LegacyQuestionFactory(display=middle_name_content)
    middle_name_question.full_clean()
    cob_content = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID + 1,
        content='City of birth',
        language_id=2,
    )
    cob_content.full_clean()
    cob_question = factories.LegacyQuestionFactory(display=cob_content)
    cob_question.full_clean()
    consent_purpose_content = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID + 2,
        content='Consent',
        language_id=2,
    )
    consent_purpose_content.full_clean()
    consent_purpose = factories.LegacyPurposeFactory(title=consent_purpose_content)
    consent_purpose.full_clean()
    # Questionnaire
    questionnaire_title = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID + 3,
        content='Databank Consent Questionnaire',
        language_id=2,
    )
    questionnaire_title.full_clean()
    consent_questionnaire = factories.LegacyQuestionnaireFactory(purpose=consent_purpose, title=questionnaire_title)
    consent_questionnaire.full_clean()
    # Questionnaire sections
    section = factories.LegacySectionFactory(questionnaire=consent_questionnaire)
    factories.LegacyQuestionSectionFactory(question=middle_name_question, section=section)
    factories.LegacyQuestionSectionFactory(question=cob_question, section=section)
    # Answer data
    answer_questionnaire = factories.LegacyAnswerQuestionnaireFactory(
        questionnaire=consent_questionnaire,
        patient=consenting_patient,
    )
    answer_questionnaire.full_clean()
    answer_section = factories.LegacyAnswerSectionFactory(answer_questionnaire=answer_questionnaire, section=section)
    cob_answer = factories.LegacyAnswerFactory(
        question=cob_question,
        answer_section=answer_section,
        patient=consenting_patient,
        questionnaire=consent_questionnaire,
    )
    middle_name_answer = factories.LegacyAnswerFactory(
        question=middle_name_question,
        answer_section=answer_section,
        patient=consenting_patient,
        questionnaire=consent_questionnaire,
    )
    factories.LegacyAnswerTextBoxFactory(answer=cob_answer, value='Springfield')
    factories.LegacyAnswerTextBoxFactory(answer=middle_name_answer, value='Juliet')

    return (consenting_patient, consent_questionnaire)


@pytest.fixture
def databank_consent_questionnaire_data() -> tuple[LegacyQuestionnaire, LegacyEducationalMaterialControl]:
    """
    Add a full databank consent questionnaire to test setup.

    Returns:
        Consent questionnaire
    """
    # Questionnaire content, content ids must be non overlapping with existing test_QuestionnaireDB SQL
    middle_name_content = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID,
        content='Middle name',
        language_id=2,
    )
    middle_name_question = factories.LegacyQuestionFactory(display=middle_name_content)
    cob_content = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID + 1,
        content='City of birth',
        language_id=2,
    )
    cob_question = factories.LegacyQuestionFactory(display=cob_content)
    consent_purpose_content = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID + 2,
        content='Consent',
        language_id=2,
    )
    consent_purpose = factories.LegacyPurposeFactory(title=consent_purpose_content)
    questionnaire_title = factories.LegacyDictionaryFactory(
        content_id=LEGACY_DICTIONARY_CONTENT_ID + 3,
        content='QSCC Databank Information',
        language_id=2,
    )
    consent_questionnaire = factories.LegacyQuestionnaireFactory(purpose=consent_purpose, title=questionnaire_title)
    section = factories.LegacySectionFactory(questionnaire=consent_questionnaire)
    factories.LegacyQuestionSectionFactory(question=middle_name_question, section=section)
    factories.LegacyQuestionSectionFactory(question=cob_question, section=section)
    legacy_factories.LegacyQuestionnaireControlFactory(
        questionnaire_name_en='QSCC Databank Information',
        questionnaire_db_ser_num=consent_questionnaire.id,
        publish_flag=1,
    )
    info_sheet = legacy_factories.LegacyEducationalMaterialControlFactory(
        educational_material_type_en='Factsheet',
        educational_material_type_fr='Fiche Descriptive',
        name_en='Information and Consent Factsheet - QSCC Databank',
        name_fr="Fiche d'information sur l'information et le consentement - Banque de données du CQSI",
    )

    return (consent_questionnaire, info_sheet)


@pytest.fixture
def set_databank_disabled(settings: LazySettings) -> None:
    """
    Fixture disables the databank for the unit test.

    Args:
        settings: the fixture providing access to the Django settings
    """
    settings.DATABANK_ENABLED = False


@pytest.fixture(autouse=True)
def set_databank_enabled(settings: LazySettings) -> None:
    """
    Fixture enables databank by default for all unit tests.

    Args:
        settings: the fixture providing access to the Django settings
    """
    settings.DATABANK_ENABLED = True
