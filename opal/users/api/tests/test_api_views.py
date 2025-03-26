"""Test module for the `users` app REST API endpoints."""
from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.users.factories import Caregiver, User

pytestmark = pytest.mark.django_db(databases=['default'])


class TestUsersCaregiversView:
    """Class wrapper for users caregivers endpoint tests."""

    def test_users_caregivers_success(self, api_client: APIClient, admin_user: User) -> None:
        """Test get patient caregivers success."""
        api_client.force_login(user=admin_user)
        username = 'test123456'
        original_email = 'email_original@opalmedapps.ca'
        updated_email = 'email_updated@opalmedapps.ca'
        caregiver = Caregiver(
            email=original_email,
            username='test123456',
            is_superuser=True,
        )

        api_client.put(
            reverse(
                'api:users-caregivers',
                kwargs={'username': username},
            ),
            data={'email': updated_email},
            format='json',
        )

        caregiver.refresh_from_db()
        assert caregiver.email == updated_email

    def test_users_caregivers_no_permission(self, api_client: APIClient) -> None:
        """Test get patient caregivers success."""
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

        api_client.put(
            reverse(
                'api:users-caregivers',
                kwargs={'username': username},
            ),
            data={'email': updated_email},
            format='json',
        )

        caregiver.refresh_from_db()
        assert caregiver.email != updated_email
