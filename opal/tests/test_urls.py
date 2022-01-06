from http import HTTPStatus

from django.test.client import Client
from django.urls.base import reverse


def test_home_not_defined(client: Client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_admin_urls_enabled():
    assert reverse('admin:index') == '/admin/'


def test_favicon_url_defined(client: Client):
    assert reverse('favicon.ico') is not None

    assert client.get('/favicon.ico').status_code != HTTPStatus.NOT_FOUND
