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
        orms_group = Group.objects.create(name=settings.ORMS_GROUP_NAME)
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

    def test_orms_login_with_missing_credentials(
        self,
        api_client: APIClient,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure the login endpoint returns an error if user does not provide username and password."""
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
        response = api_client.post(
            reverse('api:orms-login'),
            data={},
            format='json',
        )

        assertContains(
            response=response,
            text='This field is required.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_orms_login_with_wrong_credentials(
        self,
        api_client: APIClient,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure the login endpoint returns an error if user provides wrong username and password."""
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
        response = api_client.post(
            reverse('api:orms-login'),
            data={
                'username': 'wronguser',
                'password': 'wrongpass',
            },
            format='json',
        )

        assertContains(
            response=response,
            text='Unable to log in with provided credentials.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_orms_forbidden_to_login(
        self,
        api_client: APIClient,
        django_user_model: AbstractUser,
    ) -> None:
        """Ensure the login endpoint returns an error if user is not part of the 'ORMS_GROUP_NAME'."""
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

    def test_orms_multiple_requests(
        self,
        api_client: APIClient,
        django_user_model: AbstractUser,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure the endpoint handles different requests properly."""
        settings.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
        orms_group = Group.objects.create(name=settings.ORMS_GROUP_NAME)
        orms_user = django_user_model.objects.create(username='ormsuser')
        orms_user.set_password('ormspass')
        orms_user.groups.add(orms_group)
        orms_user.save()

        user = django_user_model.objects.create(username='testuser')
        user.set_password('testpass')
        user.save()

        orms_user_response = api_client.post(
            reverse('api:orms-login'),
            data={
                'username': 'ormsuser',
                'password': 'ormspass',
            },
            format='json',
        )

        user_response = api_client.post(
            reverse('api:orms-login'),
            data={
                'username': 'testuser',
                'password': 'testpass',
            },
            format='json',
        )

        assertContains(orms_user_response, 'key')
        assertContains(
            user_response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )
