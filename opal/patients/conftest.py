# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module is used to provide configuration, fixtures, and plugins for pytest."""

from django.contrib.auth.models import Permission
from django.test import Client

import pytest

from opal.users.models import User


@pytest.fixture
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


@pytest.fixture
def relationship_user(client: Client, django_user_model: User) -> Client:
    """
    Fixture provides an instance of [Client][django.test.Client] with a logged in user with relationship permission.

    Args:
        client: the Django test client instance
        django_user_model: the `User` model used in this project

    Returns:
        an instance of `Client` with a logged in user with `can_manage_relationships` permission
    """
    user = django_user_model.objects.create_user(username='test_relationship_user')
    permission = Permission.objects.get(codename='can_manage_relationships')
    user.user_permissions.add(permission)

    client.force_login(user)

    return client


@pytest.fixture
def registration_user(client: Client, django_user_model: User) -> User:
    """
    Fixture providing a `User` instance with the `can_perform_registration` permission.

    Also logs the user into the test client.
    Use this fixture together with the `client` fixture to make authenticated requests.

    Args:
        client: the Django test client instance
        django_user_model: the `User` model used in this project

    Returns:
        a user instance with the `can_perform_registration` permission
    """
    user: User = django_user_model.objects.create_user(username='test_registration_user')
    permission = Permission.objects.get(codename='can_perform_registration')
    user.user_permissions.add(permission)

    user.set_password('testpassword')
    user.save()

    client.force_login(user)

    return user


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
