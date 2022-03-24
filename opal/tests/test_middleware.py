from http import HTTPStatus

from django.test import Client
from django.urls import reverse

import pytest
from pytest_django.fixtures import SettingsWrapper

pytestmark = pytest.mark.django_db


def test_loginrequired_api_urls_excluded(client: Client, settings: SettingsWrapper) -> None:
    """Ensure that API URLs are not handled by the LoginRequiredMiddleware."""
    response = client.get('/{api_root}'.format(api_root=settings.API_ROOT))
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_loginrequired_unauthenticated_with_next(client: Client) -> None:
    """Ensure that an unauthenticated request gets redirect."""
    response = client.get(reverse('start'))

    assert response.url == '{url}?next=/'.format(url=reverse('login'))
    assert response.status_code == HTTPStatus.FOUND


def test_loginrequired_authenticated(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that authenticated requests don't get redirected to the login page."""
    response = user_client.get(reverse('start'))

    # start redirects to a default page
    assert response.status_code == HTTPStatus.FOUND
    assert response.url != reverse(settings.LOGIN_URL)


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
