"""This module is used to provide configuration, fixtures, and plugins for pytest."""
from django.contrib.auth.models import Permission

import pytest

from opal.users.models import User


@pytest.fixture
def permission_user(django_user_model: User, permission_name: str) -> User:
    """
    Fixture providing a `User` instance with the permission from the parameter.

    Args:
        django_user_model: the `User` model used in this project
        permission_name: the name of the permission

    Returns:
        a user instance with the permission from the parameter
    """
    user: User = django_user_model.objects.create_user(username='test_permission_user')
    permission = Permission.objects.get(codename=permission_name)
    user.user_permissions.add(permission)

    return user
