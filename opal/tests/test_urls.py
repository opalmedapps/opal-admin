from http import HTTPStatus

from django.test.client import Client
from django.urls.base import reverse


def test_admin_urls_enabled() -> None:
    """This test ensures that the admin URLs are enabled/available."""
    assert reverse('admin:index') == '/admin/'


def test_favicon_url_defined(client: Client) -> None:
    """This test ensures that a favicon.ico can be found by browsers."""
    assert reverse('favicon.ico') is not None

    assert client.get('/favicon.ico').status_code != HTTPStatus.NOT_FOUND
