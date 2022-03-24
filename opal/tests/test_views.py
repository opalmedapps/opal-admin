from django.test.client import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertContains
from pytest_django.fixtures import SettingsWrapper


@pytest.mark.django_db()
def test_opal_admin_url_shown(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that the OpalAdmin URL is used in the template."""
    url = 'https://example.opal'
    settings.OPAL_ADMIN_URL = url

    # follow any redirect to retrieve content
    response = user_client.get(reverse('start'), follow=True)

    assertContains(response, text='href="{url}"'.format(url=url))
