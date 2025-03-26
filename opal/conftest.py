"""This module is used to provide configuration, fixtures, and plugins for pytest."""
from pathlib import Path
from typing import Type

from django.apps import apps
from django.conf import LazySettings
from django.contrib.auth.models import Permission
from django.db import connections
from django.db.models import Model
from django.test import Client

import pytest
from pytest_django.plugin import _DatabaseBlocker  # noqa: WPS450
from rest_framework.test import APIClient

from opal.users.models import User


@pytest.fixture()
def api_client() -> APIClient:
    """
    Fixture providing an instance of Django REST framework's `APIClient`.

    Returns:
        an instance of `APIClient`
    """
    return APIClient()


@pytest.fixture()
def user_client(client: Client, django_user_model: User) -> Client:
    """
    Fixture providing an instance of [Client][django.test.Client] with a logged in user.

    Args:
        client: the Django test client instance
        django_user_model: the `User` model used in this project

    Returns:
        an instance of `Client` with a logged in user
    """
    user = django_user_model.objects.create(username='testuser')
    manage_institution_permission = Permission.objects.get(codename='can_manage_institutions')
    manage_relationship_permission = Permission.objects.get(codename='can_manage_relationships')
    manage_site_permission = Permission.objects.get(codename='can_manage_sites')
    user.user_permissions.add(manage_institution_permission)
    user.user_permissions.add(manage_relationship_permission)
    user.user_permissions.add(manage_site_permission)
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
    """Fixture changing the `MEDIA_ROOT` value of the `settings.py`.

    Args:
        tmp_path (Path): Object to a temporary directory which is unique to each test function
        settings (LazySettings): All the configurations of the `opalAdmin backend` service
    """
    settings.MEDIA_ROOT = str(tmp_path.joinpath('media/'))


@pytest.fixture(autouse=True)
def _set_email_backend_service(settings: LazySettings) -> None:
    """Fixture changing the `EMAIL_BACKEND` setting to the in-memory backend.

    Args:
        settings: the Django settings
    """
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


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
