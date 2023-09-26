"""Test module for the `users` app REST API endpoints."""
from http import HTTPStatus

from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.users.factories import Caregiver, User

pytestmark = pytest.mark.django_db(databases=['default'])


class TestUsersCaregiversUpdateView:
    """Class wrapper for users caregivers endpoint tests."""

    def test_users_caregivers_for_superuser(self, api_client: APIClient, admin_user: User) -> None:
        """Test update caregivers email address success with superuser."""
        api_client.force_login(user=admin_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        updated_email = 'email_updated@opalmedapps.ca'
        caregiver = Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        res = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={'email': updated_email},
            format='json',
        )

        caregiver.refresh_from_db()
        assert res.status_code == HTTPStatus.OK
        assert caregiver.email == updated_email

    @pytest.mark.parametrize('permission_name', ['change_caregiver'])
    def test_users_caregivers_has_permission(self, api_client: APIClient, permission_user: User) -> None:
        """Test update caregivers email address success with permission."""
        api_client.force_login(user=permission_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        updated_email = 'email_updated@opalmedapps.ca'
        caregiver = Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        res = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={'email': updated_email},
            format='json',
        )

        caregiver.refresh_from_db()
        assert res.status_code == HTTPStatus.OK
        assert caregiver.email == updated_email

    def test_users_caregivers_no_permission(self, api_client: APIClient) -> None:
        """Test update caregivers email address failure without permission."""
        user = User()
        api_client.force_login(user=user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        updated_email = 'email_updated@opalmedapps.ca'
        caregiver = Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        res = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={'email': updated_email},
            format='json',
        )

        caregiver.refresh_from_db()
        assert res.status_code == HTTPStatus.FORBIDDEN
        assert caregiver.email != updated_email

    @pytest.mark.parametrize('permission_name', ['change_caregiver'])
    def test_users_caregivers_with_empty_email(self, api_client: APIClient, permission_user: User) -> None:
        """Test update caregivers email address failure with empty email."""
        api_client.force_login(user=permission_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        caregiver = Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        res = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={'email': ''},
            format='json',
        )

        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert caregiver.email == original_email
        print(res.data)
        assert str(res.data['email']) == '{0}'.format(
            "[ErrorDetail(string='This field may not be blank.', code='blank')]",
        )

    @pytest.mark.parametrize('permission_name', ['change_caregiver'])
    def test_users_caregivers_without_email(self, api_client: APIClient, permission_user: User) -> None:
        """Test update caregivers email address failure without email."""
        api_client.force_login(user=permission_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        caregiver = Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        res = api_client.put(
            reverse(
                'api:users-caregivers-update',
                kwargs={'username': username},
            ),
            data={''},
            format='json',
        )

        assert res.status_code == HTTPStatus.BAD_REQUEST
        assert caregiver.email == original_email
        assert str(res.data['non_field_errors']) == '{0}'.format(
            "[ErrorDetail(string='Invalid data. Expected a dictionary, but got list.', code='invalid')]",
        )
