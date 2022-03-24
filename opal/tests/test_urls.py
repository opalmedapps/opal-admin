from http import HTTPStatus

from django.test.client import Client
from django.urls import resolve, reverse

import pytest
from pytest_django.fixtures import SettingsWrapper

from ..views import LoginView


def test_start_defined() -> None:
    """Ensure that a start URL is defined."""
    assert reverse('start') is not None


@pytest.mark.django_db()
def test_home_redirects(client: Client) -> None:
    """Ensure the root URL redirects somewhere."""
    response = client.get('/')

    assert response.status_code == HTTPStatus.FOUND


def test_admin_urls_enabled() -> None:
    """Ensure that the admin URLs are enabled/available."""
    assert reverse('admin:index') == '/admin/'


def test_favicon_url_defined(client: Client) -> None:
    """Ensure that a favicon.ico can be found by browsers."""
    assert reverse('favicon.ico') is not None

    assert client.get('/favicon.ico').status_code != HTTPStatus.NOT_FOUND


def test_api_auth_defined(settings: SettingsWrapper) -> None:
    """Ensure that the REST API auth endpoints are defined."""
    assert reverse('rest_login') == '/{api_root}auth/login/'.format(api_root=settings.API_ROOT)


def test_login_defined(settings: SettingsWrapper) -> None:
    """Ensure that a URL to login is defined."""
    url = reverse(settings.LOGIN_URL)
    assert url is not None
    assert resolve(url).func.__name__ == LoginView.as_view().__name__


def test_logout_defined() -> None:
    """Ensure that a URL to log out is defined."""
    assert reverse('logout') is not None
