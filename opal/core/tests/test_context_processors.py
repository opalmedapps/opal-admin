from django.http import HttpRequest

from pytest_django.fixtures import SettingsWrapper

from ..context_processors import opal_admin


def test_opal_admin_processor(settings: SettingsWrapper) -> None:
    """Ensure that the `opal_admin` context processor returns the correct dictionary."""
    url = 'https://example.opal'
    settings.OPAL_ADMIN_URL = url

    context = opal_admin(HttpRequest())
    assert all(item in {'OPAL_ADMIN_URL', 'MEDIA_URL'} for item in context)
    assert context.get('OPAL_ADMIN_URL') == url
