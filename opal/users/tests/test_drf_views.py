"""Test module for the `users` app REST API views endpoints."""
from collections.abc import Callable
from http import HTTPStatus

from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.users import factories as user_factories
from opal.users.models import User

pytestmark = pytest.mark.django_db


def test_groups_list_unauthenticated_unauthorized(api_client: APIClient, user: User) -> None:
    """Test the failure of the retrieving list of groups due to wrong permissions."""
    url = reverse('api:groups-list')

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'
    assert response.data['detail'] == 'You do not have permission to perform this action.'


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


def test_groups_list_permission_pass(
    api_client: APIClient,
    user_with_permission: Callable[[str], User],
) -> None:
    """Test the pass of the retrieving list of groups when right permissions are granted."""
    api_client.force_login(user_with_permission('auth.view_group'))
    group = user_factories.GroupFactory(name='group1')

    response = api_client.get(reverse(
        'api:groups-list',
    ))

    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 1
    assert response.data[0]['pk'] == group.pk


class TestUserCaregiverUpdateView:
    """Class wrapper for users caregivers endpoint tests."""

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        user_with_permission: Callable[[str], User],
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:users-caregivers-update', kwargs={'username': 'test'})

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(user_with_permission('users.view_caregiver'))
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_users_caregivers_for_superuser(self, api_client: APIClient, admin_user: User) -> None:
        """Test update caregivers email address success with superuser."""
        api_client.force_login(user=admin_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        updated_email = 'email_updated@opalmedapps.ca'
        caregiver = user_factories.Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        response = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={'email': updated_email},
        )

        caregiver.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert caregiver.email == updated_email

    @pytest.mark.parametrize('permission_name', ['change_caregiver'])
    def test_users_caregivers_has_permission(self, api_client: APIClient, permission_user: User) -> None:
        """Test update caregivers email address success with permission."""
        api_client.force_login(user=permission_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        updated_email = 'email_updated@opalmedapps.ca'
        caregiver = user_factories.Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        response = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={'email': updated_email},
        )

        caregiver.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert caregiver.email == updated_email

    @pytest.mark.parametrize('permission_name', ['change_caregiver'])
    def test_users_caregivers_with_empty_email(self, api_client: APIClient, permission_user: User) -> None:
        """Test update caregivers email address failure with empty email."""
        api_client.force_login(user=permission_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        caregiver = user_factories.Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        response = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={'email': ''},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert caregiver.email == original_email
        assert str(response.data['email']) == '{0}'.format(
            "[ErrorDetail(string='This field may not be blank.', code='blank')]",
        )

    @pytest.mark.parametrize('permission_name', ['change_caregiver'])
    def test_users_caregivers_without_email(self, api_client: APIClient, permission_user: User) -> None:
        """Test update caregivers email address failure without email."""
        api_client.force_login(user=permission_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        caregiver = user_factories.Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        response = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={''},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert caregiver.email == original_email
        assert str(response.data['non_field_errors']) == '{0}'.format(
            "[ErrorDetail(string='Invalid data. Expected a dictionary, but got list.', code='invalid')]",
        )
