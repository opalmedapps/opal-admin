"""This module is used to provide configuration, fixtures, and plugins for pytest."""
from django.contrib.auth.models import Permission
from django.test import Client

import pytest

from opal.users.models import User


@pytest.fixture()
def relationshiptype_user(client: Client, django_user_model: User) -> Client:
    """
    Fixture provides an instance of [Client][django.test.Client] with a logged in user with relationshiptype permission.

    Args:
        client: the Django test client instance
        django_user_model: the `User` model used in this project

    Returns:
        an instance of `Client` with a logged in user with `can_manage_relationshiptype` permission
    """
    user = django_user_model.objects.create_user(username='test_relationshiptype_user')
    permission = Permission.objects.get(codename='can_manage_relationshiptypes')
    user.user_permissions.add(permission)

    client.force_login(user)

    return client
