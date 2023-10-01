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
