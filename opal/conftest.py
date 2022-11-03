"""This module is used to provide configuration, fixtures, and plugins for pytest."""
from pathlib import Path
from typing import Any, Type

from django.apps import apps
from django.conf import LazySettings
from django.db import connections
from django.db.models import Model
from django.test import Client

import pytest
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


@pytest.fixture(scope='session', autouse=True)
def _django_db_setup(django_db_setup: Any, django_db_blocker: Any, django_db_keepdb: bool) -> None:
    """Add test_QuestionnaireDB setup by executing code in tests/sql.

    Args:
        django_db_blocker (Any): pytest fixture to allow database access here only
    """
    from django.conf import settings  # noqa: WPS433
    print(settings.DATABASES['questionnaire'])
    print(django_db_keepdb)
    print(connections['questionnaire'])
    # db_name = f"test_{settings.DATABASES['questionnaire']['NAME']}"
    # settings.DATABASES['questionnaire']['NAME'] =
    # load test questionnaire db sql
    if not django_db_keepdb:
        with open('opal/tests/sql/test_QuestionnaireDB_.sql', encoding='ISO-8859-1') as handle:
            sql_content = handle.read()
            handle.close()

        with django_db_blocker.unblock():
            with connections['questionnaire'].cursor() as conn:
                conn.execute(sql_content)
                conn.close()
