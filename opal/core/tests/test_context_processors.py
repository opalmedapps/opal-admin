from django.http import HttpRequest

from pytest_django.fixtures import SettingsWrapper

from ..context_processors import opal_global_settings


def test_admin_url_in_context_processor(settings: SettingsWrapper) -> None:
    """Ensure that the `opal_global_settings` context processor returns the OPAL_ADMIN_URL value."""
    url = 'https://example.opal'
    settings.OPAL_ADMIN_URL = url

    context = opal_global_settings(HttpRequest())
    assert 'OPAL_ADMIN_URL' in context
    assert context.get('OPAL_ADMIN_URL') == url


def test_media_url_in_context_processor(settings: SettingsWrapper) -> None:
    """Ensure that the `opal_global_settings` context processor returns the MEDIA_URL value."""
    url = '/test-media/'
    settings.MEDIA_URL = url

    context = opal_global_settings(HttpRequest())
    assert 'MEDIA_URL' in context
    assert context.get('MEDIA_URL') == url
