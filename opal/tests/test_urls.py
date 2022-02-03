from http import HTTPStatus

from django.test.client import Client
from django.urls.base import reverse

import pytest


def test_start_defined():
    """This test ensures that a start URL is defined."""
    assert reverse('start') is not None


@pytest.mark.django_db()
def test_home_redirects(client: Client):
    """This test ensures the root URL redirects somewhere."""
    response = client.get('/')

    assert response.status_code == HTTPStatus.FOUND


def test_admin_urls_enabled():
    """This test ensures that the admin URLs are enabled/available."""
    assert reverse('admin:index') == '/admin/'


def test_favicon_url_defined(client: Client):
    """This test ensures that a favicon.ico can be found by browsers."""
    assert reverse('favicon.ico') is not None

    assert client.get('/favicon.ico').status_code != HTTPStatus.NOT_FOUND
