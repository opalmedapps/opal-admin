"""Test module for the `users` app REST API urls endpoints."""
from django.urls import resolve, reverse

import pytest

pytestmark = pytest.mark.django_db


def test_groups_list() -> None:
    """Ensure groups list is defined."""
    assert reverse('api:groups-list') == '/api/groups/'
    assert resolve('/api/groups/').view_name == 'api:groups-list'
