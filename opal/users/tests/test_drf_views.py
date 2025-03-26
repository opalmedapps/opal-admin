"""Test module for the `users` app REST API views endpoints."""
from http import HTTPStatus

from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.users import factories as user_factories
from opal.users.models import User

pytestmark = pytest.mark.django_db


def test_groups_list_pass(api_client: APIClient, admin_user: User) -> None:
    """Test the pass of the retrieving list of groups."""
    api_client.force_login(user=admin_user)
    user_factories.GroupFactory(name='group1')
    user_factories.GroupFactory(name='group2')

    response = api_client.get(reverse(
        'api:groups-list',
    ))
    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 2
