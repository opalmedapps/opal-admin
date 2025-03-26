from http import HTTPStatus

from django.test.client import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertContains, assertRedirects
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from rest_framework.test import APIClient

from opal.users.models import User

from .. import views

pytestmark = pytest.mark.django_db()


def test_opal_admin_url_shown(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that the OpalAdmin URL is used in the template."""
    url = 'https://example.opal'
    settings.OPAL_ADMIN_URL = url

    # follow any redirect to retrieve content
    response = user_client.get(reverse('start'), follow=True)

    assertContains(response, text='href="{url}/#!/home"'.format(url=url))


def test_logout_url_shown(user_client: Client) -> None:
    """Ensure that the logout URL is used in the template."""
    # follow any redirect to retrieve content
    response = user_client.get(reverse('start'), follow=True)

    assertContains(response, text='method="post" action="{url}"'.format(url=reverse('logout')))


def test_unauthenticated_redirected(client: Client, settings: SettingsWrapper) -> None:
    """Ensure that an unauthenticated request to the redirect URL is redirected to the login page."""
    response = client.get(reverse(settings.LOGIN_REDIRECT_URL))

    assertRedirects(response, '{url}?next=/'.format(url=reverse(settings.LOGIN_URL)))


def test_loginview_success(client: Client, django_user_model: User, settings: SettingsWrapper) -> None:
    """Ensure that submitting the login form with correct credentials authenticates the user."""
    credentials = {
        'username': 'testuser',
        'password': 'testpass',
    }
    user = django_user_model.objects.create(username=credentials['username'])
    user.set_password(credentials['password'])
    user.save()

    response = client.post(
        reverse(settings.LOGIN_URL),
        data=credentials,
    )

    assertRedirects(
        response,
        expected_url=reverse(settings.LOGIN_REDIRECT_URL),
        target_status_code=HTTPStatus.FOUND,
    )


def test_loginview_error(client: Client, settings: SettingsWrapper, mocker: MockerFixture) -> None:
    """Ensure that submitting the login form with incorrect credentials fails authenticating the user."""
    # assume that the FedAuthBackend is enabled and remove it (to avoid making outgoing requests during tests)
    # if it is not enabled in the future, remove these lines
    assert 'opal.core.auth.FedAuthBackend' in settings.AUTHENTICATION_BACKENDS
    # mock authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend.authenticate')
    mock_authenticate.return_value = None

    credentials = {
        'username': 'testuser',
        'password': 'invalid',
    }

    response = client.post(
        reverse(settings.LOGIN_URL),
        data=credentials,
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, 'class="errornote"')
    assertContains(
        response,
        'Please enter a correct username and password. Note that both fields may be case-sensitive.',
    )


def test_logout_redirects(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that a logged in user can log out and that it redirects to the main OpalAdmin URL."""
    settings.LOGOUT_REDIRECT_URL = 'http://foobar.com'
    response = user_client.post(reverse('logout'))

    assertRedirects(
        response,
        expected_url='http://foobar.com',
        target_status_code=HTTPStatus.FOUND,
        fetch_redirect_response=False,
    )

    assert not response.wsgi_request.user.is_authenticated


def test_createupdateview_create(django_user_model: User) -> None:
    """The `CreateUpdateView` can handle creation of a new object."""
    # simulate a create
    view: views.CreateUpdateView[User] = views.CreateUpdateView(
        queryset=django_user_model.objects.all(),
    )

    assert view.get_object() is None


def test_createupdateview_update(django_user_model: User) -> None:
    """The `CreateUpdateView` can handle updating an existing object."""
    user = django_user_model.objects.create(username='testuser')

    # simulate an update for a specific object
    view: views.CreateUpdateView[User] = views.CreateUpdateView(
        queryset=django_user_model.objects.all(),
        kwargs={'pk': user.pk},
    )

    assert view.get_object() == user


def test_languagesview_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    registration_listener_user: User,
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    url = reverse('api:languages')

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(registration_listener_user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.OK


def test_languagesview_get(
    admin_api_client: APIClient,
    settings: SettingsWrapper,
) -> None:
    """Ensure that the `LanguagesView` can return the languages in the settings."""
    settings.LANGUAGES = [
        ('lan1', 'language1'),
        ('lan2', 'language2'),
    ]
    response = admin_api_client.get(reverse('api:languages'))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {'code': 'lan1', 'name': 'language1'},
        {'code': 'lan2', 'name': 'language2'},
    ]
