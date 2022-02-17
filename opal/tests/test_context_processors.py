from django.http import HttpRequest

from ..context_processors import opal_admin


def test_opal_admin_processor(settings):
    """This test ensures that the `opal_admin` context processor returns the correct setting."""
    url = 'https://example.opal'
    settings.OPAL_ADMIN_URL = url

    context = opal_admin(HttpRequest())

    assert 'OPAL_ADMIN_URL' in context
    assert context.get('OPAL_ADMIN_URL') == url
