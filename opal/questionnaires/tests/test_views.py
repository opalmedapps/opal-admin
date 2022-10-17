from http import HTTPStatus
from typing import Tuple

from django.contrib.auth.models import AbstractUser
from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertTemplateUsed, assertURLEqual

from opal.users.models import User

pytestmark = pytest.mark.django_db


# All questionnaires templates and their associated url
test_url_template_data: list[Tuple] = [
    (reverse('questionnaires:index'), 'questionnaires/index.html'),
    (reverse('questionnaires:exportreports-list'), 'questionnaires/export_reports/exportreports-list.html'),
    (reverse('questionnaires:exportreports-query'), 'questionnaires/export_reports/exportreports-query.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_questionnaire_urls_exist(user_client: Client, admin_user: AbstractUser, url: str, template: str) -> None:
    """Ensure that a page exists at each URL address."""
    user_client.force_login(admin_user)
    response = user_client.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_views_use_correct_template(user_client: Client, admin_user: AbstractUser, url: str, template: str) -> None:
    """Ensure that a page uses appropriate templates."""
    user_client.force_login(admin_user)
    response = user_client.get(url)

    assertTemplateUsed(response, template)


def test_list_select_form_exists(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a form exists in the reports page and it contains the correct URL."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:exportreports-list'))
    soup = BeautifulSoup(response.content, 'html.parser')
    forms = soup.find_all('form')

    assert response.status_code == HTTPStatus.OK
    assertURLEqual(forms[0].get('action'), reverse('questionnaires:exportreports-query'))


def test_query_viewreport_form_exists(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a form exists in the reports page and it contains the correct URL."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:exportreports-query'))
    soup = BeautifulSoup(response.content, 'html.parser')
    forms = soup.find_all('form')

    assert response.status_code == HTTPStatus.OK
    assertURLEqual(forms[0].get('action'), reverse('questionnaires:exportreports-viewreport'))


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
