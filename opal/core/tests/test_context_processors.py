from django.http import HttpRequest
from django.test.client import Client
from django.urls import reverse

import pytest
from pytest_django.fixtures import SettingsWrapper

from opal.core import context_processors


def test_admin_url_in_context_processor(settings: SettingsWrapper) -> None:
    """Ensure that the `opal_global_settings` context processor returns the OPAL_ADMIN_URL value."""
    url = 'https://example.opal'
    settings.OPAL_ADMIN_URL = url

    context = context_processors.opal_global_settings(HttpRequest())
    assert 'OPAL_ADMIN_URL' in context
    assert context.get('OPAL_ADMIN_URL') == url


def test_current_app_no_resolver() -> None:
    """Ensure that the `current_app` context processor can handle a `None` resolver_match."""
    context = context_processors.current_app(HttpRequest())

    assert 'app_verbose_name' not in context


@pytest.mark.django_db
def test_current_app_verbose_name_no_app(client: Client) -> None:
    """Ensure that the `current_app` context processor can handle a `None` app_name."""
    response = client.get(reverse('start'))
    # HttpResponse also
    context = context_processors.current_app(response)  # type: ignore[arg-type]

    assert 'app_verbose_name' not in context


@pytest.mark.django_db
def test_current_app_verbose_name(client: Client) -> None:
    """Ensure that the `current_app` context processor can return the current app's verbose name."""
    response = client.get(reverse('admin:index'))
    context = context_processors.current_app(response)  # type: ignore[arg-type]

    assert 'app_verbose_name' in context
    assert context['app_verbose_name'] == 'Administration'
