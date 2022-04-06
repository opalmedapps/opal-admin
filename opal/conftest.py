"""This module is used to provide configuration, fixtures, and plugins for pytest."""
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
