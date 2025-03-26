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
    group = user_factories.GroupFactory(name='group1')
    user_factories.GroupFactory(name='group2')

    response = api_client.get(reverse(
        'api:groups-list',
    ))
    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 2
    assert response.data[0]['pk'] == group.pk


def test_groups_list_fail(api_client: APIClient, django_user_model: User) -> None:
    """Test the failure of the retrieving list of groups due to wrong permissions."""
    user = django_user_model.objects.create(username='test_user')
    api_client.force_login(user=user)
    user_factories.GroupFactory(name='group1')

    response = api_client.get(reverse(
        'api:groups-list',
    ))
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.data['detail'] == 'You do not have permission to perform this action.'
