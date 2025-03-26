from datetime import date
from http import HTTPStatus
from typing import Tuple

from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from easyaudit.models import RequestEvent
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from opal.questionnaires.factories import QuestionnaireProfile as QuestionnaireProfileFactory
from opal.questionnaires.models import QuestionnaireProfile
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


# Add any future GET-requestable questionnaire pages here for faster test writing
test_url_template_data: list[Tuple] = [
    (reverse('questionnaires:index'), 'questionnaires/index.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_questionnaire_urls_exist(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page exists at each URL address."""
    response = admin_client.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_views_use_correct_template(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page uses appropriate templates."""
    response = admin_client.get(url)

    assertTemplateUsed(response, template)


def test_dashboard_empty_profile(admin_client: Client) -> None:
    """Ensure that the dashboard doesnt crash if no profile exists for the user."""
    response = admin_client.get(reverse('questionnaires:reports'))
    assert response.status_code == HTTPStatus.OK


def test_dashboard_forms_exist(user_client: Client) -> None:
    """Ensure that forms exist in the dashboard page pointing to the list & filter pages."""
    test_questionnaire_profile = QuestionnaireProfileFactory()  # Get test user & profile from factory
    test_questionnaire_profile.user.is_superuser = True  # Permission to view report tooling
    test_questionnaire_profile.user.save()
    user_client.force_login(test_questionnaire_profile.user)

    response = user_client.get(reverse('questionnaires:reports'))

    assertContains(response, reverse('questionnaires:reports-filter'))
    assertContains(response, reverse('questionnaires:reports-list'))


def test_dashboard_multi_questionnaire_profile(user_client: Client) -> None:
    """Ensure that forms exist in the dashboard page pointing to the list & filter pages."""
    test_questionnaire_profile = QuestionnaireProfileFactory()
    test_questionnaire_profile.user.is_superuser = True
    test_questionnaire_profile.user.save()
    user_client.force_login(test_questionnaire_profile.user)

    response = user_client.get(reverse('questionnaires:reports'))

    assert response.status_code == HTTPStatus.OK

    #  Add second questionnaire to list and go back to dashboard page
    QuestionnaireProfile.update_questionnaires_following(
        qid='13',
        qname='Test Add Questionnaire',
        user=test_questionnaire_profile.user,
        toggle=True,
    )

    response = user_client.get(reverse('questionnaires:reports'))

    assert response.status_code == HTTPStatus.OK


def test_filter_report_form_exists(admin_client: Client) -> None:
    """Ensure that a form exists in the reports list page pointing to the filter page."""
    response = admin_client.get(reverse('questionnaires:reports-list'))
    assertContains(response, reverse('questionnaires:reports-filter'))


def test_detail_report_form_exists(user_client: Client) -> None:
    """Ensure that a form exists in the reports filter page pointing to the detail page."""
    test_questionnaire_profile = QuestionnaireProfileFactory()  # Get test user & profile from factory
    test_questionnaire_profile.user.is_superuser = True  # Permission to view report tooling
    test_questionnaire_profile.user.save()
    user_client.force_login(test_questionnaire_profile.user)

    response = user_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={'questionnaireid': ['11']},
    )

    assertContains(response, reverse('questionnaires:reports-detail'))


def test_download_forms_exist(admin_client: Client) -> None:
    """Ensure that forms exists in the reports detail page and they point to the two download options."""
    response = admin_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={
            'start': ['2016-11-25'],
            'end': ['2020-02-27'],
            'patientIDs': ['3'],
            'questionIDs': ['823', '824', '811', '830', '832'],
            'questionnaireid': ['11'],
            'questionnairename': ['Test Qst'],
            'following': [True],
        },
    )

    assertContains(response, reverse('questionnaires:reports-download-csv'))
    assertContains(response, reverse('questionnaires:reports-download-xlsx'))


def test_filter_report_invalid_params(admin_client: Client) -> None:
    """Ensure that a post call to filter reports returns error given invalid/missing params."""
    response = admin_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_detail_report_invalid_params(admin_client: Client) -> None:
    """Ensure that a post call to detail reports returns error given invalid/missing params."""
    response = admin_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_export_report_hidden_unauthenticated(user_client: Client, django_user_model: User) -> None:
    """Ensure that an unauthenticated (not admin) user can't view the Export Reports page."""
    user = django_user_model.objects.create(username='test_export_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    export_url = reverse('questionnaires:reports')

    assertNotContains(response, f'href="{export_url}"')


@pytest.mark.xfail(condition=True, reason='the sidebar menus are removed', strict=True)
def test_export_report_visible_authenticated(admin_client: Client) -> None:
    """Ensure that an authenticated user can view the Export Reports page."""
    response = admin_client.get(reverse('hospital-settings:index'))

    export_url = reverse('questionnaires:reports')
    assertContains(response, f'href="{export_url}"')


def test_questionnaires_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that the questionnaires menu is not displayed for users without necessary permissions."""
    user = django_user_model.objects.create(username='test_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    soup = BeautifulSoup(response.content, 'html.parser')
    menu_group = soup.find_all(
        'button',
        attrs={'class': 'btn-toggle'},
        string=lambda value: 'Questionnaires' in value,
    )

    assert not menu_group


def test_get_reports_filter_unauthorized(admin_client: Client) -> None:
    """Ensure no GET requests can be made to the page."""
    response = admin_client.get(reverse('questionnaires:reports-filter'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_get_detail_unauthorized(admin_client: Client) -> None:
    """Ensure no GET requests can be made to the page."""
    response = admin_client.get(reverse('questionnaires:reports-detail'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_get_downloadcsv_viewreport_unauthorized(admin_client: Client) -> None:
    """Ensure no GET requests can be made to the page."""
    response = admin_client.get(reverse('questionnaires:reports-download-csv'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_get_downloadxlsx_viewreport_unauthorized(admin_client: Client) -> None:
    """Ensure no GET requests can be made to the page."""
    response = admin_client.get(reverse('questionnaires:reports-download-xlsx'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_reportlist_visible_authenticated(admin_client: Client) -> None:
    """Ensure that an authenticated user can view the Export Reports page."""
    response = admin_client.get(reverse('questionnaires:reports-list'))

    assert response.status_code == HTTPStatus.OK


def test_report_filter_invalid_key_format(admin_client: Client) -> None:
    """Ensure bad request error if bad key format."""
    response = admin_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={'questionnaireid': ['fish']},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_report_filter_missing_key(admin_client: Client) -> None:
    """Ensure bad request error if missing key."""
    response = admin_client.post(
        path=reverse('questionnaires:reports-filter'),
        data={'badkey': ['11']},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_request_event_filter_template(user_client: Client) -> None:
    """Ensure RequestEvent object is correctly updated on call to filter template."""
    test_questionnaire_profile = QuestionnaireProfileFactory()  # Get test user & profile from factory
    test_questionnaire_profile.user.is_superuser = True  # Permission to view report tooling
    test_questionnaire_profile.user.save()
    user_client.force_login(test_questionnaire_profile.user)

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


def test_update_request_event_detail_template(admin_client: Client) -> None:
    """Ensure RequestEvent object is correctly updated on call to detail template."""
    response = admin_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={
            'start': ['2016-11-25'],
            'end': ['2020-02-27'],
            'patientIDs': ['3'],
            'questionIDs': ['823', '824', '811', '830', '832'],
            'questionnaireid': ['11'],
            'questionnairename': ['Test Qst'],
        },
    )
    q_string = (
        "{'questionnaireid': '11', 'start': '2016-11-25', 'end': '2020-02-27',"
        + " 'patientIDs': '3', 'questionIDs': '832'}"
    )
    method = 'POST'
    request_event = RequestEvent.objects.filter(
        url='/questionnaires/reports/detail/',
    ).order_by('-datetime').first()

    assert response.status_code == HTTPStatus.OK
    assert request_event.method == method
    assert request_event.query_string == q_string


def test_detail_template_download_csv(admin_client: Client) -> None:
    """Ensure downloading of csv data works as expected."""
    # trigger generation of temp tables
    response = admin_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={
            'start': ['2016-11-25'],
            'end': ['2020-02-27'],
            'patientIDs': ['3'],
            'questionIDs': ['823', '824', '811', '830', '832'],
            'questionnaireid': ['11'],
            'questionnairename': ['Test Qst'],
        },
    )
    assert response.status_code == HTTPStatus.OK
    response = admin_client.post(
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


def test_detail_template_download_xlsx(admin_client: Client) -> None:
    """Ensure downloading of xlsx data works as expected."""
    # trigger generation of temp tables
    response = admin_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={
            'start': ['2016-11-25'],
            'end': ['2020-02-27'],
            'patientIDs': ['3'],
            'questionIDs': ['823', '824', '811', '830', '832'],
            'questionnaireid': ['11'],
            'questionnairename': ['Test Qst'],
        },
    )

    assert response.status_code == HTTPStatus.OK
    response_one = admin_client.post(
        path=reverse('questionnaires:reports-download-xlsx'),
        data={
            'questionnaireid': ['11'],
            'tabs': ['none'],
        },
    )
    response_two = admin_client.post(
        path=reverse('questionnaires:reports-download-xlsx'),
        data={
            'questionnaireid': ['11'],
            'tabs': ['patients'],
        },
    )
    response_three = admin_client.post(
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


def test_toggle_questionnaire_follow(admin_client: Client) -> None:
    """Ensure that the update questionnaire profile method works from the view call."""
    admin_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={
            'start': ['2016-11-25'],
            'end': ['2020-02-27'],
            'patientIDs': ['3'],
            'questionIDs': ['823', '824', '811', '830', '832'],
            'questionnaireid': ['11'],
            'questionnairename': ['Test Qst'],
            'following': [True],
            'toggle': [True],
        },
    )

    response = admin_client.post(
        path=reverse('questionnaires:reports-detail'),
        data={
            'start': ['2016-11-25'],
            'end': ['2020-02-27'],
            'patientIDs': ['3'],
            'questionIDs': ['823', '824', '811', '830', '832'],
            'questionnaireid': ['11'],
            'questionnairename': ['Test Qst'],
            'following': [True],
            'toggle': [False],
        },
    )

    assert response.status_code == HTTPStatus.OK
