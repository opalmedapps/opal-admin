import json
from http import HTTPStatus
from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.test.client import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual, assertRaisesMessage, assertRedirects
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from opal.core.api.views import EmptyResponseSerializer
from opal.hospital_settings import factories as hospital_factories
from opal.hospital_settings.models import Site
from opal.patients import factories as patient_factories
from opal.users.models import User

from .. import views

pytestmark = pytest.mark.django_db()

PATIENT_UUID = uuid4()
FIXTURES_DIR = Path(__file__).resolve().parent.joinpath(
    'fixtures',
)


def test_opal_admin_url_shown(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that the OpalAdmin URL is used in the template."""
    url = 'https://example.opal'
    settings.OPAL_ADMIN_URL = url

    # follow any redirect to retrieve content
    response = user_client.get(reverse('start'), follow=True)

    assertContains(response, text=f'href="{url}/#!/home"')


def test_logout_url_shown(user_client: Client) -> None:
    """Ensure that the logout URL is used in the template."""
    # follow any redirect to retrieve content
    response = user_client.get(reverse('start'), follow=True)

    assertContains(response, text='method="post" action="{url}"'.format(url=reverse('logout')))


@pytest.mark.xfail(condition=True, reason='the home page link are changed', strict=True)
def test_home_url_shown(user_client: Client) -> None:
    """Ensure that the template shows a link to the home page."""
    # follow any redirect to retrieve content
    response = user_client.get(reverse('start'), follow=True)

    assertContains(response, text='href="{url}"'.format(url=reverse('start')))


def test_unauthenticated_redirected(client: Client, settings: SettingsWrapper) -> None:
    """Ensure that an unauthenticated request to the redirect URL is redirected to the login page."""
    response = client.get(reverse(settings.LOGIN_REDIRECT_URL))

    assertRedirects(response, f'{reverse(settings.LOGIN_URL)}?next=/')


def test_loginview_success(client: Client, django_user_model: User, settings: SettingsWrapper) -> None:
    """Ensure that submitting the login form with correct credentials authenticates the user."""
    credentials = {
        'username': 'testuser',
        'password': 'testpass',
    }
    user = django_user_model.objects.create(username=credentials['username'])
    user.set_password(credentials['password'])
    user.save()

    response = client.post(
        reverse(settings.LOGIN_URL),
        data=credentials,
    )

    assertRedirects(
        response,
        expected_url=reverse(settings.LOGIN_REDIRECT_URL),
        target_status_code=HTTPStatus.FOUND,
    )


def test_loginview_error(client: Client, settings: SettingsWrapper, mocker: MockerFixture) -> None:
    """Ensure that submitting the login form with incorrect credentials fails authenticating the user."""
    # assume that the FedAuthBackend is enabled and remove it (to avoid making outgoing requests during tests)
    # if it is not enabled in the future, remove these lines
    assert 'opal.core.auth.FedAuthBackend' in settings.AUTHENTICATION_BACKENDS
    # mock authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend.authenticate')
    mock_authenticate.return_value = None

    credentials = {
        'username': 'testuser',
        'password': 'invalid',
    }

    response = client.post(
        reverse(settings.LOGIN_URL),
        data=credentials,
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, 'class="errornote"')
    assertContains(
        response,
        'Please enter a correct username and password. Note that both fields may be case-sensitive.',
    )


def test_logout_redirects(user_client: Client, settings: SettingsWrapper) -> None:
    """Ensure that a logged in user can log out and that it redirects to the main OpalAdmin URL."""
    settings.LOGOUT_REDIRECT_URL = 'http://foobar.com'
    response = user_client.post(reverse('logout'))

    assertRedirects(
        response,
        expected_url='http://foobar.com',
        target_status_code=HTTPStatus.FOUND,
        fetch_redirect_response=False,
    )

    assert not response.wsgi_request.user.is_authenticated


def test_createupdateview_create(django_user_model: User) -> None:
    """The `CreateUpdateView` can handle creation of a new object."""
    # simulate a create
    view: views.CreateUpdateView[User] = views.CreateUpdateView(
        queryset=django_user_model.objects.all(),
    )

    assert view.get_object() is None


def test_createupdateview_update(django_user_model: User) -> None:
    """The `CreateUpdateView` can handle updating an existing object."""
    user = django_user_model.objects.create(username='testuser')

    # simulate an update for a specific object
    view: views.CreateUpdateView[User] = views.CreateUpdateView(
        queryset=django_user_model.objects.all(),
        kwargs={'pk': user.pk},
    )

    assert view.get_object() == user


def test_languagesview_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    registration_listener_user: User,
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    url = reverse('api:languages')

    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(registration_listener_user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.OK


def test_languagesview_get(
    admin_api_client: APIClient,
    settings: SettingsWrapper,
) -> None:
    """Ensure that the `LanguagesView` can return the languages in the settings."""
    settings.LANGUAGES = [
        ('lan1', 'language1'),
        ('lan2', 'language2'),
    ]
    response = admin_api_client.get(reverse('api:languages'))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {'code': 'lan1', 'name': 'language1'},
        {'code': 'lan2', 'name': 'language2'},
    ]


def test_hl7_create_view_pid_does_not_match_uuid(
    api_client: APIClient,
    interface_engine_user: User,
) -> None:
    """Ensure the endpoint returns an error if patient identified in the PID doesn't match the uuid in the url."""
    api_client.force_login(interface_engine_user)
    patient = patient_factories.Patient(
        ramq='TEST01161972',
        uuid=PATIENT_UUID,
    )
    hospital_factories.Site(acronym='RVH')
    patient_factories.HospitalPatient(
        patient=patient,
        site=Site.objects.get(acronym='RVH'),
        mrn='9999996',
    )

    response = api_client.post(
        reverse('api:patient-pharmacy-create', kwargs={'uuid': uuid4()}),
        data=_load_hl7_fixture('marge_pharmacy.hl7v2'),
        content_type='application/hl7-v2+er7',
    )
    assertJSONEqual(
        raw=json.dumps(response.json()),
        expected_data={
            'status': 'error',
            'message': 'PID segment data did not match uuid provided in url.',
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_hl7_create_view_patient_not_found_by_pid_data(
    api_client: APIClient,
    interface_engine_user: User,
) -> None:
    """Ensure the endpoint returns an error if the PID data does not yield a valid and unique patient."""
    api_client.force_login(interface_engine_user)
    hospital_factories.Site(acronym='RVH')
    message = 'Patient identified by HL7 PID could not be uniquely found in database.'
    with assertRaisesMessage(ValidationError, message):
        api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': PATIENT_UUID}),
            data=_load_hl7_fixture('marge_pharmacy.hl7v2'),
            content_type='application/hl7-v2+er7',
        )


def _load_hl7_fixture(filename: str) -> str:
    """Load a HL7 fixture for testing.

    Returns:
        string of the fixture data
    """
    with (FIXTURES_DIR / filename).open('r') as file:
        return file.read()


def test_empty_response_serializer() -> None:
    """Ensure the EmptyResponseSerializer data is empty and valid."""
    serializer = EmptyResponseSerializer(data={})
    assert serializer.is_valid(), 'Serializer should be valid for empty data'
    assert not serializer.data, 'Serialized data should be an empty dictionary'
