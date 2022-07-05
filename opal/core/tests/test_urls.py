from http import HTTPStatus
from typing import Type

from django.contrib.auth.views import LogoutView
from django.test.client import Client
from django.urls import resolve, reverse

import pytest
from pytest_django.fixtures import SettingsWrapper

from opal.core.views import LoginView


def assert_path_uses_view(path: str, view_class: Type) -> None:
    """
    Assert that the view resolved via the provided path uses the given view class.

    Makes use of the fully qualified name of the view function.
    """
    full_name = '.'.join([view_class.__module__, view_class.__qualname__])
    assert resolve(path)._func_path == full_name


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


@pytest.mark.django_db()
def test_favicon_url_defined(client: Client) -> None:
    """Ensure that a favicon.ico can be found by browsers."""
    assert reverse('favicon.ico') is not None

    assert client.get('/favicon.ico').status_code != HTTPStatus.NOT_FOUND


def test_login_defined(settings: SettingsWrapper) -> None:
    """Ensure that a URL to login is defined."""
    path = reverse(settings.LOGIN_URL)
    assert path is not None
    assert_path_uses_view(path, LoginView)


def test_logout_defined() -> None:
    """Ensure that a URL to log out is defined."""
    path = reverse('logout')
    assert reverse('logout') is not None
    assert_path_uses_view(path, LogoutView)
