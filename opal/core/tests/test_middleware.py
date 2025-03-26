from http import HTTPStatus

from django.test import Client
from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from ..middleware import LoginRequiredMiddleware

pytestmark = pytest.mark.django_db


def test_loginrequired_api_urls_excluded(client: Client, settings: SettingsWrapper) -> None:
    """Ensure that API URLs are not handled by the LoginRequiredMiddleware."""
    assert 'api:rest_logout' not in settings.AUTH_EXEMPT_ROUTES

    response = client.get(reverse('api:rest_logout'))
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_loginrequired_partial_urls_not_excluded(
    client: Client,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    """Ensure that API URLs are not handled by the LoginRequiredMiddleware."""
    mock_resolve_route = mocker.spy(LoginRequiredMiddleware, '_resolve_route')

    # ensure that the middleware excludes /{api_root}/ only
    response = client.get(f'/{settings.API_ROOT}test')
    mock_resolve_route.assert_called_once()

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_loginrequired_unauthenticated_with_next(client: Client) -> None:
    """Ensure that an unauthenticated request gets redirect."""
    response = client.get(reverse('start'))

    assertRedirects(response, '{url}?next=/'.format(url=reverse('login')))


def test_loginrequired_authenticated(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that authenticated requests don't get redirected to the login page."""
    response = user_client.get(reverse('start'))

    # start redirects to a default page
    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] != reverse(settings.LOGIN_URL)


def test_loginrequired_unauthenticated_open_url(client: Client, settings: SettingsWrapper) -> None:
    """Ensure that open URLs are exempted for unauthenticated requests."""
    response = client.get(reverse(settings.LOGIN_URL))

    assert response.status_code == HTTPStatus.OK


def test_loginrequired_unauthenticated_favicon(client: Client, settings: SettingsWrapper) -> None:
    """Ensure that open URLs are exempted for unauthenticated requests."""
    response = client.get(reverse('favicon.ico'))

    assert response.status_code == HTTPStatus.MOVED_PERMANENTLY


def test_loginrequired_url_namespace(client: Client) -> None:
    """Ensure that URLs with a namespace get resolved properly."""
    response = client.get(reverse('admin:login'))

    assert response.status_code == HTTPStatus.OK
