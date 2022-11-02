from http import HTTPStatus
from typing import Tuple

from django.contrib.auth.models import AbstractUser
from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertTemplateUsed, assertURLEqual

from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


# Add any future GET-requestable questionnaire pages here for faster test writing
test_url_template_data: list[Tuple] = [
    (reverse('questionnaires:index'), 'questionnaires/index.html'),
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


def test_reportlist_urls_exist(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a page exists at each URL address."""
    user_client.force_login(admin_user)
    url = reverse('questionnaires:reports-list', kwargs={'username': admin_user.username})
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_filter_report_form_exists(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a form exists in the reports page and it contains the correct URL."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:reports-list', kwargs={'username': admin_user.username}))
    soup = BeautifulSoup(response.content, 'html.parser')
    forms = soup.find_all('form')

    assert response.status_code == HTTPStatus.OK
    assertURLEqual(forms[0].get('action'), reverse('questionnaires:reports-filter'))


def test_detail_report_form_exists(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a form exists in the reports page and it contains the correct URL."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={'questionnaireid': ['11']},
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    forms = soup.find_all('form')

    assert response.status_code == HTTPStatus.OK
    assertURLEqual(forms[0].get('action'), reverse('questionnaires:reports-detail'))


def test_download_forms_exist(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a form exists in the reports page and it contains the correct URL."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={
            'start': ['2016-11-25'],
            'end': ['2020-02-27'],
            'patientIDs': ['3'],
            'questionIDs': ['823', '824', '811', '830', '832'],
            'questionnaireid': ['11'],
        },
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    forms = soup.find_all('form')

    assert response.status_code == HTTPStatus.OK
    assertURLEqual(forms[0].get('action'), reverse('questionnaires:reports-download-csv'))
    assertURLEqual(forms[1].get('action'), reverse('questionnaires:reports-download-xlsx'))


def test_filter_report_invalid_params(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a post call to filter reports returns error given invalid/missing params."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_detail_report_invalid_params(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a post call to detail reports returns error given invalid/missing params."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_download_csv_valid_content(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a post call to download csv returns correct content."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-download-csv'),
        data={
            'questionnaireid': ['11'],
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response['content-type'] == 'text/csv'


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


def test_get_exportreports_query_unauthorized(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure no GET requests can be made to the page."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:reports-filter'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_get_viewreport_unauthorized(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure no GET requests can be made to the page."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:reports-detail'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_get_downloadcsv_viewreport_unauthorized(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure no GET requests can be made to the page."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:reports-download-csv'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_get_downloadxlsx_viewreport_unauthorized(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure no GET requests can be made to the page."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:reports-download-xlsx'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_reportlist_visible_authenticated(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that an authenticated user can view the Export Reports page."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:reports-list', kwargs={'username': admin_user.username}))

    assert response.status_code == HTTPStatus.OK
