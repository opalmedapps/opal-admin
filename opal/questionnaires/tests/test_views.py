from datetime import date
from http import HTTPStatus
from typing import Tuple

from django.contrib.auth.models import AbstractUser
from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from easyaudit.models import RequestEvent
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


def test_filter_report_form_exists(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a form exists in the reports list page pointing to the filter page."""
    user_client.force_login(admin_user)
    response = user_client.get(reverse('questionnaires:reports-list'))
    soup = BeautifulSoup(response.content, 'html.parser')
    forms = soup.find_all('form')

    assert response.status_code == HTTPStatus.OK
    assertURLEqual(forms[0].get('action'), reverse('questionnaires:reports-filter'))


def test_detail_report_form_exists(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure that a form exists in the reports filter page pointing to the detail page."""
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
    """Ensure that forms exists in the reports detail page and they point to the two download options."""
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
    response = user_client.get(reverse('questionnaires:reports-list'))

    assert response.status_code == HTTPStatus.OK


def test_report_filter_invalid_key_format(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure bad request error if bad key format."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={'questionnaireid': ['fish']},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_report_filter_missing_key(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure bad request error if missing key."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={'badkey': ['11']},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_request_event_filter_template(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure RequestEvent object is correctly updated on call to filter template."""
    user_client.force_login(admin_user)
    response = user_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={'questionnaireid': ['11']},
    )
    q_string = "{'questionnaireid': '11'}"
    method = 'POST'
    request_event = RequestEvent.objects.filter(
        url='/questionnaires/reports/filter/',
    ).order_by('-datetime').first()

    assert response.status_code == HTTPStatus.OK
    assert request_event.method == method
    assert request_event.query_string == q_string


def test_update_request_event_detail_template(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure RequestEvent object is correctly updated on call to detail template."""
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
    q_string = "{'questionnaireid': '11', 'start': '2016-11-25', 'end': '2020-02-27', 'patientIDs': '3', 'questionIDs': '832'}"  # noqa: E501
    method = 'POST'
    request_event = RequestEvent.objects.filter(
        url='/questionnaires/reports/detail/',
    ).order_by('-datetime').first()

    assert response.status_code == HTTPStatus.OK
    assert request_event.method == method
    assert request_event.query_string == q_string


def test_detail_template_download_csv(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure downloading of csv data works as expected."""
    user_client.force_login(admin_user)
    # trigger generation of temp tables
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
    assert response.status_code == HTTPStatus.OK
    response = user_client.post(
        path=reverse('questionnaires:reports-download-csv'),
        data={
            'questionnaireid': ['11'],
        },
    )
    assert response.status_code == HTTPStatus.OK
    headers = response.headers
    assert headers.get('Content-Type') == 'text/csv'
    filename = f'attachment; filename = questionnaire-11-{date.today().isoformat()}.csv'  # noqa: WPS237
    assert headers.get('Content-Disposition') == filename
    assert int(headers.get('Content-Length', 0)) > 0


def test_detail_template_download_xlsx(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure downloading of xlsx data works as expected."""
    user_client.force_login(admin_user)
    # trigger generation of temp tables
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
    assert response.status_code == HTTPStatus.OK
    response_one = user_client.post(
        path=reverse('questionnaires:reports-download-xlsx'),
        data={
            'questionnaireid': ['11'],
            'tabs': ['none'],
        },
    )
    response_two = user_client.post(
        path=reverse('questionnaires:reports-download-xlsx'),
        data={
            'questionnaireid': ['11'],
            'tabs': ['patients'],
        },
    )
    response_three = user_client.post(
        path=reverse('questionnaires:reports-download-xlsx'),
        data={
            'questionnaireid': ['11'],
            'tabs': ['questions'],
        },
    )
    for resp in (response_one, response_two, response_three):
        assert resp.status_code == HTTPStatus.OK
    for header in (response_one.headers, response_two.headers, response_three.headers):
        assert header.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f'attachment; filename = questionnaire-11-{date.today().isoformat()}.xlsx'  # noqa: WPS237
        assert header.get('Content-Disposition') == filename
        assert int(header.get('Content-Length', 0)) > 0
