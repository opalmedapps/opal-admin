from django.contrib.auth.models import Group
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient

from opal.users.models import User

pytestmark = pytest.mark.django_db


class TestORMSLoginView:
    """Class wrapper for ORMS auth/login tests."""

    def test_orms_login_success(
        self,
        api_client: APIClient,
        django_user_model: User,
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
        )

        assertContains(
            response=response,
            text='Unable to log in with provided credentials.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_orms_forbidden_to_login(
        self,
        api_client: APIClient,
        django_user_model: User,
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
        )

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_orms_multiple_requests(
        self,
        api_client: APIClient,
        django_user_model: User,
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
        )

        user_response = api_client.post(
            reverse('api:orms-login'),
            data={
                'username': 'testuser',
                'password': 'testpass',
            },
        )

        assertContains(orms_user_response, 'key')
        assertContains(
            user_response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )


class TestORMSValidateView:
    """Class wrapper for ORMS auth/validate session tests."""

    def test_unauthenticated(self, api_client: APIClient) -> None:
        """Ensure that unauthenticated requests don't succeeed."""
        response = api_client.get(reverse('api:orms-validate'))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_orms_validate_session_success(
        self,
        api_client: APIClient,
        user: User,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure the session is validated successfully."""
        orms_group = Group.objects.create(name=settings.ORMS_GROUP_NAME)
        api_client.force_login(user=user)
        user.groups.add(orms_group)
        user.first_name = 'firstname'
        user.last_name = 'lastname'
        user.save()

        response = api_client.get(reverse('api:orms-validate'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'username': 'testuser', 'first_name': 'firstname', 'last_name': 'lastname'}

    def test_orms_validate_session_no_permission(
        self,
        api_client: APIClient,
        user: User,
    ) -> None:
        """Ensure the validate endpoint raise an exception if user is not part of the 'ORMS_GROUP_NAME'."""
        api_client.force_login(user=user)

        response = api_client.get(reverse('api:orms-validate'))

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )
