from http import HTTPStatus

from django.test.client import Client
from django.urls.base import reverse

import pytest


def test_start_defined():
    assert reverse('start') is not None


@pytest.mark.django_db
def test_home_redirects(client: Client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.FOUND


def test_admin_urls_enabled():
    assert reverse('admin:index') == '/admin/'


def test_favicon_url_defined(client: Client):
    assert reverse('favicon.ico') is not None

    assert client.get('/favicon.ico').status_code != HTTPStatus.NOT_FOUND
