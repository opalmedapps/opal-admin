from django.contrib.auth.models import AbstractUser, Group
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestORMSLoginView:
    """Class wrapper for ORMS auth/login tests."""

    def test_orms_login_success(
        self,
        api_client: APIClient,
        django_user_model: AbstractUser,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure a user can successfully login."""
        orms_group = Group.objects.create(name=settings.ORMS_USER_GROUP)
        user = django_user_model.objects.create(username='testuser')
        user.set_password('testpass')
        user.groups.add(orms_group)
        user.save()

        response = api_client.post(
            reverse('api:orms-login'),
            data={
                'username': 'testuser',
                'password': 'testpass',
            },
            format='json',
        )

        assertContains(response, 'key')

    def test_orms_unable_to_login(
        self,
        api_client: APIClient,
        django_user_model: AbstractUser,
    ) -> None:
        """Ensure the login endpoint returns an error if user is not part of the 'ORMS_USER_GROUP'."""
        user = django_user_model.objects.create(username='testuser')
        user.set_password('testpass')
        user.save()

        response = api_client.post(
            reverse('api:orms-login'),
            data={
                'username': 'testuser',
                'password': 'testpass',
            },
            format='json',
        )

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )
