"""Test module for the `users` app REST API urls endpoints."""
from django.urls import resolve, reverse

import pytest

from opal.users import factories

pytestmark = pytest.mark.django_db


def test_groups_list() -> None:
    """Ensure groups list is defined."""
    assert reverse('api:groups-list') == '/api/groups/'
    assert resolve('/api/groups/').view_name == 'api:groups-list'


def test_users_list() -> None:
    """Ensure users list is defined."""
    assert reverse('api:users-list') == '/api/users/'
    assert resolve('/api/users/').view_name == 'api:users-list'


def test_users_detail() -> None:
    """Ensure users detail is defined."""
    user = factories.User()

    assert reverse(
        'api:users-detail',
        kwargs={'username': user.username},
    ) == f'/api/users/{user.username}/'  # noqa: WPS221
    assert resolve(f'/api/users/{user.username}/').view_name == 'api:users-detail'


def test_users_action_set_manager_user() -> None:
    """Ensure users action for `set-manager-user` is defined."""
    user = factories.User()

    assert reverse(
        'api:users-set-manager-user',
        kwargs={'username': user.username},
    ) == f'/api/users/{user.username}/set-manager-user/'

    assert resolve(f'/api/users/{user.username}/set-manager-user/').view_name == 'api:users-set-manager-user'


def test_users_action_unset_manager_user() -> None:
    """Ensure users action for `unset-manager-user` is defined."""
    user = factories.User()

    assert reverse(
        'api:users-unset-manager-user',
        kwargs={'username': user.username},
    ) == f'/api/users/{user.username}/unset-manager-user/'

    assert resolve(f'/api/users/{user.username}/unset-manager-user/').view_name == 'api:users-unset-manager-user'


def test_users_action_deactivate_user() -> None:
    """Ensure users action for `deactivate-user` is defined."""
    user = factories.User()

    assert reverse(
        'api:users-deactivate-user',
        kwargs={'username': user.username},
    ) == f'/api/users/{user.username}/deactivate-user/'

    assert resolve(f'/api/users/{user.username}/deactivate-user/').view_name == 'api:users-deactivate-user'


def test_users_action_reactivate_user() -> None:
    """Ensure users action for `reactivate-user` is defined."""
    user = factories.User()

    assert reverse(
        'api:users-reactivate-user',
        kwargs={'username': user.username},
    ) == f'/api/users/{user.username}/reactivate-user/'

    assert resolve(f'/api/users/{user.username}/reactivate-user/').view_name == 'api:users-reactivate-user'
