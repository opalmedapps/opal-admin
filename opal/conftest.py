"""This module is used to provide configuration, fixtures, and plugins for pytest."""
from pathlib import Path
from typing import Type

from django.apps import apps
from django.conf import LazySettings
from django.db import connections
from django.db.models import Model
from django.test import Client

import pytest
from _pytest.config import Config
from _pytest.main import Session
from _pytest.python import Function, Module
from pytest_django.plugin import _DatabaseBlocker
from rest_framework.test import APIClient

from opal.users.models import User


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
    items[:] = original_items_order + migration_tests  # noqa: WPS362


@pytest.fixture()
def api_client() -> APIClient:
    """
    Fixture providing an instance of Django REST framework's `APIClient`.

    Returns:
        an instance of `APIClient`
    """
    return APIClient()


@pytest.fixture()
def user_api_client(api_client: APIClient, django_user_model: User) -> APIClient:  # noqa: WPS442
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


@pytest.fixture()
def admin_api_client(api_client: APIClient, admin_user: User) -> APIClient:  # noqa: WPS442
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
@pytest.fixture()
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


def is_legacy_model(model: Type[Model]) -> bool:
    """
    Determine whether the given model is a legacy model.

    Only models from the legacy app that are unmanaged are legacy models.

    Args:
        model: the model to check

    Returns:
        `True`, if it is a legacy model, `False` otherwise
    """
    return model._meta.app_label == 'legacy' and not model._meta.managed  # noqa: WPS437


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
        model._meta.managed = True  # noqa: WPS437


@pytest.fixture(autouse=True)
def _change_media_root(tmp_path: Path, settings: LazySettings) -> None:
    """Fixture changing the `MEDIA_ROOT` value of the settings.

    Args:
        tmp_path: Object to a temporary directory which is unique to each test function
        settings: All the configurations of the `opalAdmin backend` service
    """
    settings.MEDIA_ROOT = str(tmp_path.joinpath('media/'))


@pytest.fixture(scope='session', autouse=True)
def django_db_setup(django_db_setup: None, django_db_blocker: _DatabaseBlocker) -> None:  # noqa: PT004, WPS442
    """Add test_QuestionnaireDB setup by executing code in tests/sql.

    Args:
        django_db_setup: pytest django's original DB setup fixture
        django_db_blocker: pytest fixture to allow database access here only
    """
    # load test questionnaire db sql
    with Path('opal/tests/sql/test_QuestionnaireDB.sql', encoding='ISO-8859-1').open() as handle:
        sql_content = handle.read()
        handle.close()

    with django_db_blocker.unblock():
        with connections['questionnaire'].cursor() as conn:
            conn.execute(sql_content)
            conn.close()
