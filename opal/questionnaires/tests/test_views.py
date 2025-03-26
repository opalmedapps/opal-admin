from http import HTTPStatus
from typing import Tuple

from django.contrib.auth.models import AbstractUser
from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertRedirects, assertURLEqual
from pytest_django.fixtures import SettingsWrapper

from opal.users.models import User

pytestmark = pytest.mark.django_db


# All questionnaires templates and their associated url
test_url_template_data: list[Tuple] = [
    (reverse('questionnaires:index'), 'questionnaires/index.html'),
    (reverse('questionnaires:exportreports'), 'questionnaires/export_reports/exportreports.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_questionnaire_urls_exist(user_client: Client, url: str, template: str) -> None:
    """Ensure that a page exists at each URL address."""
    response = user_client.get(url)

    assert response.status_code == HTTPStatus.OK


def test_export_report_launch_redirects(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that after clicking the ePRO button, the page redirects to the reporting tool."""
    response = user_client.get(reverse('questionnaires:exportreports-launch'))

    assertRedirects(
        response,
        expected_url=settings.EPRO_DATA_EXTRACTIONS_URL,
        target_status_code=HTTPStatus.FOUND,
        fetch_redirect_response=False,
    )


def test_export_report_launch_url_exists(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a button exists in the reports page and it contains the correct URL."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:exportreports'))
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a', attrs={'class': 'btn btn-primary mr-2'})

    assert response.status_code == HTTPStatus.OK
    assertURLEqual(links[0].get('href'), reverse('questionnaires:exportreports-launch'))


def test_export_report_hidden_unauthenticated(user_client: Client, django_user_model: User) -> None:
    """Ensure that an unauthenticated (not admin) user can't view the Export Reports page."""
    user = django_user_model.objects.create(username='test_export_user')
    user_client.force_login(user)
    response = user_client.get(reverse('hospital-settings:index'))
    soup = BeautifulSoup(response.content, 'html.parser')
    pages_available = soup.find_all('p', {'class': 'text'})

    assert response.status_code == HTTPStatus.OK
    assert 'Export Reports' not in {pagename.text for pagename in pages_available}


def test_export_report_visible_authenticated(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that an authenticated user can view the Export Reports page."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('hospital-settings:index'))
    soup = BeautifulSoup(response.content, 'html.parser')
    pages_available = soup.find_all('p', {'class': 'text'})

    assert response.status_code == HTTPStatus.OK
    assert 'Export Reports' in {pagename.text for pagename in pages_available}
