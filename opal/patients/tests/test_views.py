import io
import re
import urllib
from datetime import date, datetime
from http import HTTPStatus
from typing import Any, Tuple

from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.http import HttpRequest
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils.html import strip_tags

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains, assertNotContains, assertQuerysetEqual, assertTemplateUsed
from pytest_mock.plugin import MockerFixture

from opal.caregivers.models import CaregiverProfile
from opal.hospital_settings.models import Site
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData
from opal.users.factories import Caregiver
from opal.users.models import User

from .. import constants, factories, forms, models, tables
# Add any future GET-requestable patients app pages here for faster test writing
from ..views import AccessRequestView, ManageCaregiverAccessListView, ManageCaregiverAccessUpdateView

pytestmark = pytest.mark.django_db

CUSTOMIZED_OIE_PATIENT_DATA = OIEPatientData(
    date_of_birth=date.fromisoformat('1984-05-09'),
    first_name='Marge',
    last_name='Simpson',
    sex='F',
    alias='',
    deceased=False,
    death_date_time=datetime.strptime('2054-05-09 09:20:30', '%Y-%m-%d %H:%M:%S'),
    ramq='MARG99991313',
    ramq_expiration=datetime.strptime('2024-01-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
    mrns=[
        OIEMRNData(
            site='MGH',
            mrn='9999993',
            active=True,
        ),
        OIEMRNData(
            site='MCH',
            mrn='9999994',
            active=True,
        ),
        OIEMRNData(
            site='RVH',
            mrn='9999993',
            active=True,
        ),
    ],
)

test_url_template_data: list[Tuple] = [
    (reverse('patients:relationships-list'), 'patients/relationships/pending_relationship_list.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_patients_urls_exist(user_client: Client, admin_user: AbstractUser, url: str, template: str) -> None:
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


def test_relationshiptypes_list_table(relationshiptype_user: Client) -> None:
    """Relationship types list uses the corresponding table."""
    response = relationshiptype_user.get(reverse('patients:relationshiptype-list'))

    assert response.context['table'].__class__ == tables.RelationshipTypeTable


def test_relationshiptypes_list(relationshiptype_user: Client) -> None:
    """Relationship types are listed."""
    types = [factories.RelationshipType(), factories.RelationshipType(name='Second')]

    response = relationshiptype_user.get(reverse('patients:relationshiptype-list'))
    response.content.decode('utf-8')

    assertQuerysetEqual(
        response.context['relationshiptype_list'].order_by('name'),
        models.RelationshipType.objects.all(),
    )

    for relationship_type in types:
        assertContains(response, f'<td >{relationship_type.name}</td>')


def test_relationshiptype_create_get(relationshiptype_user: Client) -> None:
    """A new relationship type can be created in a form."""
    response = relationshiptype_user.get(reverse('patients:relationshiptype-create'))

    assertContains(response, 'Create Relationship Type')


def test_relationshiptype_create(relationshiptype_user: Client) -> None:
    """A new relationship type can be created."""
    relationship_type = factories.RelationshipType.build(name='Testname')

    relationshiptype_user.post(
        reverse('patients:relationshiptype-create'),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )
    assert models.RelationshipType.objects.count() == 5
    assert models.RelationshipType.objects.get(name='Testname').name == relationship_type.name


def test_relationshiptype_update_get(relationshiptype_user: Client) -> None:
    """An existing relationship type can be edited."""
    relationship_type = factories.RelationshipType()
    response = relationshiptype_user.get(
        reverse('patients:relationshiptype-update', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )
    assertContains(response, 'Update Relationship Type')
    assertContains(response, 'value="Caregiver"')


def test_relationshiptype_update_post(relationshiptype_user: Client) -> None:
    """An existing relationship type can be updated."""
    relationship_type = factories.RelationshipType()

    relationship_type.end_age = 100

    relationshiptype_user.post(
        reverse('patients:relationshiptype-update', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id']),
    )

    assert models.RelationshipType.objects.get(pk=relationship_type.pk).end_age == 100


def test_relationshiptype_delete_get(relationshiptype_user: Client) -> None:
    """Deleting a relationship type needs to be confirmed."""
    relationship_type = factories.RelationshipType()

    response = relationshiptype_user.get(
        reverse('patients:relationshiptype-delete', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )
    assertContains(response, 'Are you sure you want to delete "Caregiver"?')


def test_relationshiptype_delete(relationshiptype_user: Client) -> None:
    """An existing relationship type can be deleted."""
    relationship_type = factories.RelationshipType()

    relationshiptype_user.delete(
        reverse('patients:relationshiptype-delete', kwargs={'pk': relationship_type.pk}),
    )

    assert models.RelationshipType.objects.count() == 4


# tuple with patients wizard form templates and corresponding url names
test_patient_multiform_url_template_data: list[Tuple] = [
    ('patients:access-request', 'patients/access_request/access_request.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_initial_call(
    registration_user: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that steps are called initially."""
    url = reverse(url_name)
    response = registration_user.get(url)
    wizard = response.context['wizard']

    assert response.status_code == HTTPStatus.OK
    assert wizard['steps'].current == 'site'
    assert wizard['steps'].last == 'password'
    assert wizard['steps'].next == 'search'
    assert wizard['steps'].count == 8


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_post_error(
    registration_user: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the validation error happens with the form if the field is missing value."""
    url = reverse(url_name)
    step_one_data = {
        'access_request_view-current_step': 'site',
    }
    response = registration_user.post(url, step_one_data)

    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'
    assert response.context['wizard']['form'].errors == {'sites': ['This field is required.']}


def _wizard_step_data(site: Site) -> Tuple[dict, dict, dict, dict, dict]:
    return (
        {
            'site-sites': site.pk,
            'access_request_view-current_step': 'site',
        },
        {
            'search-medical_card': constants.MedicalCard.RAMQ.name,
            'search-medical_number': 'RAMQ99996666',
            'access_request_view-current_step': 'search',
        },
        {
            'confirm-is_correct': True,
            'access_request_view-current_step': 'confirm',
        },
        {
            'relationship-relationship_type': factories.RelationshipType().pk,
            'access_request_view-current_step': 'relationship',
        },
        {
            'account-user_type': 0,
            'access_request_view-current_step': 'account',
        },
    )


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_post_mgmt_data_missing(
    registration_user: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the form return bad request if the management data is missing."""
    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    wizard_step_one_data = wizard_step_data[0].copy()
    # remove management data
    for key in list(wizard_step_one_data.keys()):
        if 'current_step' in key:
            wizard_step_one_data.pop(key)

    response = registration_user.post(url, wizard_step_one_data)
    # view should return HTTP 400 Bad Request
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_post_success(
    registration_user: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the form submission with POST is successful."""
    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    response = registration_user.post(url, wizard_step_data[0])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'search'
    assert response.context['wizard']['steps'].step0 == 1
    assert response.context['wizard']['steps'].prev == 'site'
    assert response.context['wizard']['steps'].next == 'confirm'


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_stepback(
    registration_user: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the form can go back to the previous step."""
    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    response = registration_user.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'

    response = registration_user.post(url, wizard_step_data[0])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'search'

    response = registration_user.post(url, {
        'wizard_goto_step': response.context['wizard']['steps'].prev,
    })
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_finish(
    registration_user: Client,
    url_name: str,
    template: str,
    mocker: MockerFixture,
) -> None:
    """Ensure that the form can go through all the steps."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': CUSTOMIZED_OIE_PATIENT_DATA,
        },
    )

    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    response = registration_user.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'
    assert response.context['header_title'] == 'Hospital Information'

    response = registration_user.post(url, wizard_step_data[0])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'search'
    assert response.context['header_title'] == 'Patient Details'

    response = registration_user.post(url, wizard_step_data[1])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'confirm'
    assert response.context['header_title'] == 'Patient Details'

    response = registration_user.post(url, wizard_step_data[2])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'relationship'
    assert response.context['header_title'] == 'Requestor Details'


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_error_in_template(
    registration_user: Client,
    url_name: str,
    template: str,
    mocker: MockerFixture,
) -> None:
    """Ensure that the error message shows up when mrns records with the same site code."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': OIEPatientData(
                date_of_birth=date.fromisoformat('1984-05-09'),
                first_name='Marge',
                last_name='Simpson',
                sex='F',
                alias='',
                deceased=False,
                death_date_time=datetime.strptime('2054-05-09 09:20:30', '%Y-%m-%d %H:%M:%S'),
                ramq='MARG99991313',
                ramq_expiration=datetime.strptime('2024-01-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
                mrns=[
                    OIEMRNData(
                        site='MGH',
                        mrn='9999993',
                        active=True,
                    ),
                    OIEMRNData(
                        site='MGH',
                        mrn='9999994',
                        active=True,
                    ),
                ],
            ),
        },
    )

    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    response = registration_user.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'
    assert response.context['header_title'] == 'Hospital Information'

    response = registration_user.post(url, wizard_step_data[1])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'confirm'
    assert response.context['header_title'] == 'Patient Details'
    assert response.context['error_message'] == 'Please note multiple MRNs need to be merged by medical records.'
    assertTemplateUsed(response, template)


def test_access_request_done_redirects_temp(  # noqa: C901 WPS231
    registration_user: Client,
    mocker: MockerFixture,
) -> None:
    """Ensure that when the page is submitted it redirects to the final page."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': CUSTOMIZED_OIE_PATIENT_DATA,
        },
    )

    # mock fed authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = ('user@example.com', 'First', 'Last')

    url = reverse('patients:access-request')
    site = factories.Site()
    relationship = factories.RelationshipType()
    user = Caregiver(email='marge.simpson@gmail.com', phone_number='+15141111111')
    factories.Patient(ramq='MARG99991313')
    factories.CaregiverProfile(user_id=user.id)
    form_data = [
        ('site', {'sites': site.pk}),
        ('search', {'medical_card': constants.MedicalCard.RAMQ.name, 'medical_number': 'MARG99991313'}),
        ('confirm', {'is_correct': True}),
        ('relationship', {'relationship_type': relationship.pk, 'requestor_form': False}),
        ('account', {'user_type': '1'}),
        ('requestor', {'user_email': 'marge.simpson@gmail.com', 'user_phone': '+15141111111'}),
        ('existing', {'is_correct': True, 'is_id_checked': True}),
        ('password', {'confirm_password': 'testpassword'}),
    ]
    response = registration_user.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'

    for step, step_data in form_data:
        step_data = {
            '{0}-{1}'.format(step, key): value
            for key, value in step_data.items()
        }
        step_data['access_request_view-current_step'] = step
        response = registration_user.post(url, step_data, follow=True)
        assert response.status_code == HTTPStatus.OK

        if 'site' in step:  # noqa: WPS223
            assert response.context['wizard']['steps'].current == 'search'
        elif 'search' in step:
            assert response.context['wizard']['steps'].current == 'confirm'
        elif 'confirm' in step:
            assert response.context['wizard']['steps'].current == 'relationship'
        elif 'relationship' in step:
            assert response.context['wizard']['steps'].current == 'account'
        elif 'account' in step:
            assert response.context['wizard']['steps'].current == 'requestor'
        elif 'requestor' in step:
            assert response.context['wizard']['steps'].current == 'existing'
        elif 'existing' in step:
            assert response.context['wizard']['steps'].current == 'password'
        elif 'password' in step:
            assertTemplateUsed(response, 'patients/access_request/confirmation_code.html')


class _TestAccessRequestView(AccessRequestView):
    """
    This view is to test AccessRequestView.

    It patches dispatch to return the view instance as well for testing.

    It requires since the WizardView needs to be fully set up.
    """

    def dispatch(   # type: ignore[override]
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[Any, '_TestAccessRequestView']:
        """
        Process the request.

        Args:
            request: a `HttpRequest` instance
            args: additional keyword arguments
            kwargs: additional keyword arguments

        Returns:
            the object of HttpResponse
        """
        response = super().dispatch(request, *args, **kwargs)
        return response, self

    def dummy_get_response(self, request: HttpRequest) -> None:  # noqa: WPS324
        """
        Pass `None` for the middleware get_response argument.

        Args:
            request: a `HttpRequest` instance

        Returns:
            None
        """
        return None  # noqa: WPS324


def _init_session(registration_user: Client) -> HttpRequest:
    """
    Initialize the session.

    Returns:
        the request
    """
    response = registration_user.get(reverse('patients:access-request'))
    request = RequestFactory().get(response)  # type: ignore[arg-type]
    request.user = response.context['user']

    # adding session
    middleware = SessionMiddleware(_TestAccessRequestView.dummy_get_response)  # type: ignore[arg-type]
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db()
def test_unexpected_step(registration_user: Client) -> None:
    """Test unexpected step 'confirm'."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('confirm') == {}  # noqa: WPS520


@pytest.mark.django_db()
def test_search_step_with_valid_id_in_session(registration_user: Client) -> None:
    """Test expected step 'search' with session storage of saving user selection."""
    request = _init_session(registration_user)
    request.session['site_selection'] = 2
    # adding Site records
    factories.Site(pk=1)
    factories.Site(pk=2)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('search') == {
        'site_code': Site.objects.get(pk=2).code,
    }


@pytest.mark.django_db()
def test_search_step_with_invalid_id_in_session(registration_user: Client) -> None:
    """Test expected step 'search' with an invalid session storage of saving user selection."""
    request = _init_session(registration_user)
    request.session['site_selection'] = 3
    # adding Site records
    factories.Site(pk=1)
    factories.Site(pk=2)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('search') == {}  # noqa: WPS520


@pytest.mark.django_db()
def test_expected_step_without_session_storage(registration_user: Client) -> None:
    """Test expected step 'site' without session storage of saving user selection."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('site') == {}  # noqa: WPS520


@pytest.mark.django_db()
def test_site_step_with_valid_id_in_session(registration_user: Client) -> None:
    """Test expected step 'site' with session storage of saving user selection."""
    request = _init_session(registration_user)
    request.session['site_selection'] = 2
    # adding Site records
    factories.Site(pk=1)
    factories.Site(pk=2)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('site') == {
        'sites': Site.objects.filter(pk=2).first(),
    }


@pytest.mark.django_db()
def test_site_step_with_invalid_id_in_session(registration_user: Client) -> None:
    """Test expected step 'site' with an invalid session storage of saving user selection."""
    request = _init_session(registration_user)
    request.session['site_selection'] = 3
    # adding Site records
    factories.Site(pk=1)
    factories.Site(pk=2)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('site') == {}  # noqa: WPS520


@pytest.mark.django_db()
def test_process_step_select_site_form(registration_user: Client) -> None:
    """Test expected form 'SelectSiteForm'."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    site = factories.Site()
    form_data = (
        {
            'site-sites': site.pk,
        }
    )
    form = forms.SelectSiteForm(data=form_data)

    assert response.status_code == HTTPStatus.OK
    assert instance.process_step(form) == form_data
    assert request.session['site_selection'] == site.pk


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_new_user_form_by_user_choice(
    registration_user: Client,
    url_name: str,
    template: str,
    mocker: MockerFixture,
) -> None:
    """Test get_form function returns a `NewUserForm` form by the user choice."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': CUSTOMIZED_OIE_PATIENT_DATA,
        },
    )

    url = reverse(url_name)
    site = factories.Site()
    relationship = factories.RelationshipType()
    form_data = [
        ('site', {'sites': site.pk}),
        ('search', {'medical_card': constants.MedicalCard.RAMQ.name, 'medical_number': 'MARG99991313'}),
        ('confirm', {'is_correct': True}),
        ('relationship', {'relationship_type': relationship.pk, 'requestor_form': False}),
        ('account', {'user_type': 0}),
    ]
    response = registration_user.get(url)
    for step, step_data in form_data:
        step_data = {
            '{0}-{1}'.format(step, key): value
            for key, value in step_data.items()
        }
        step_data['access_request_view-current_step'] = step
        response = registration_user.post(url, step_data, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['form'].__class__ == forms.NewUserForm


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_existing_user_form_by_user_choice(
    registration_user: Client,
    url_name: str,
    template: str,
    mocker: MockerFixture,
) -> None:
    """Test get_form function returns a `ExistingUserForm` form by the user choice."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': CUSTOMIZED_OIE_PATIENT_DATA,
        },
    )

    url = reverse(url_name)
    site = factories.Site()
    relationship = factories.RelationshipType()
    form_data = [
        ('site', {'sites': site.pk}),
        ('search', {'medical_card': constants.MedicalCard.RAMQ.name, 'medical_number': 'MARG99991313'}),
        ('confirm', {'is_correct': True}),
        ('relationship', {'relationship_type': relationship.pk, 'requestor_form': False}),
        ('account', {'user_type': 1}),
    ]
    response = registration_user.get(url)
    for step, step_data in form_data:
        step_data = {
            '{0}-{1}'.format(step, key): value
            for key, value in step_data.items()
        }
        step_data['access_request_view-current_step'] = step
        response = registration_user.post(url, step_data, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['form'].__class__ == forms.ExistingUserForm
    # to assert it contains the area code initialization in the phone number field
    assertContains(response, 'name="requestor-user_phone" value="+1"')


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_new_user_case_in_password_step(
    registration_user: Client,
    url_name: str,
    template: str,
    mocker: MockerFixture,
) -> None:
    """Test get_form function returns a `ConfirmPasswordForm` form once the new user requests."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': CUSTOMIZED_OIE_PATIENT_DATA,
        },
    )

    url = reverse(url_name)
    site = factories.Site()
    relationship = factories.RelationshipType()

    form_data = [
        ('site', {'sites': site.pk}),
        ('search', {'medical_card': constants.MedicalCard.RAMQ.name, 'medical_number': 'MARG99991313'}),
        ('confirm', {'is_correct': True}),
        ('relationship', {'relationship_type': relationship.pk, 'requestor_form': False}),
        ('account', {'user_type': 0}),
        ('requestor', {'first_name': 'Marge', 'last_name': 'Simpson', 'is_id_checked': True}),
    ]
    response = registration_user.get(url)
    for step, step_data in form_data:
        step_data = {
            '{0}-{1}'.format(step, key): value
            for key, value in step_data.items()
        }
        step_data['access_request_view-current_step'] = step
        response = registration_user.post(url, step_data, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['form'].__class__ == forms.ConfirmPasswordForm


@pytest.mark.django_db()
def test_create_caregiver_profile_existing_user(registration_user: Client) -> None:
    """Test create caregiver profile for the existing user."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    form_data = {
        'user_type': '1',
        'user_email': 'marge.simpson@gmail.com',
        'user_phone': '+15141111111',
    }

    caregiver_user = Caregiver(email='marge.simpson@gmail.com', phone_number='+15141111111')
    caregiver = factories.CaregiverProfile(user_id=caregiver_user.id)

    assert response.status_code == HTTPStatus.OK
    assert instance._create_caregiver_profile(
        form_data=form_data,
        random_username_length=constants.USERNAME_LENGTH,
    ) == {'caregiver_user': caregiver_user, 'caregiver': caregiver}


@pytest.mark.django_db()
def test_create_caregiver_profile_failed(registration_user: Client) -> None:
    """Test create caregiver profile failed for the existing user."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    form_data = {
        'user_type': '1',
        'user_email': 'test.simpson@gmail.com',
        'user_phone': '+15141111111',
    }

    assert response.status_code == HTTPStatus.OK
    assert instance._create_caregiver_profile(
        form_data=form_data,
        random_username_length=constants.USERNAME_LENGTH,
    ) == {}     # noqa: WPS520


@pytest.mark.django_db()
def test_create_caregiver_profile_new_user(registration_user: Client) -> None:
    """Test create caregiver profile for the new user."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    form_data = {
        'user_type': '0',
        'first_name': 'Marge',
        'last_name': 'Simpson',
    }

    caregiver_dict = instance._create_caregiver_profile(
        form_data=form_data,
        random_username_length=constants.USERNAME_LENGTH,
    )
    caregiver = CaregiverProfile(user=caregiver_dict['caregiver_user'])

    assert response.status_code == HTTPStatus.OK
    assert str(caregiver) == '{0}, {1}'.format(
        form_data['last_name'],
        form_data['first_name'],
    )


@pytest.mark.django_db()
def test_create_patient(registration_user: Client) -> None:
    """Test create patient instance."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    form_data = {
        'patient_record': CUSTOMIZED_OIE_PATIENT_DATA,
    }
    patient = instance._create_patient(form_data=form_data)

    assert response.status_code == HTTPStatus.OK
    assert patient.ramq == CUSTOMIZED_OIE_PATIENT_DATA.ramq
    assert patient.sex == CUSTOMIZED_OIE_PATIENT_DATA.sex
    assert patient.date_of_birth == CUSTOMIZED_OIE_PATIENT_DATA.date_of_birth
    assert str(patient) == '{0}, {1}'.format(
        CUSTOMIZED_OIE_PATIENT_DATA.last_name,
        CUSTOMIZED_OIE_PATIENT_DATA.first_name,
    )


@pytest.mark.django_db()
def test_get_current_relationship(registration_user: Client) -> None:
    """Test get an existing relationship instance."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    form_data = {
        'user_type': '1',
        'user_email': 'marge.simpson@gmail.com',
        'user_phone': '+15141111111',
        'patient_record': CUSTOMIZED_OIE_PATIENT_DATA,
        'relationship_type': factories.RelationshipType(name='Self'),
    }

    caregiver_user = Caregiver(email=form_data['user_email'], phone_number=form_data['user_phone'])
    caregiver = factories.CaregiverProfile(user_id=caregiver_user.id)

    caregiver_dict = instance._create_caregiver_profile(
        form_data=form_data,
        random_username_length=constants.USERNAME_LENGTH,
    )

    patient = instance._create_patient(form_data=form_data)

    factories.Relationship(type=form_data['relationship_type'], caregiver=caregiver, patient=patient)

    relationship = instance._create_relationship(
        form_data=form_data,
        caregiver_dict=caregiver_dict,
        patient=patient,
    )

    assert response.status_code == HTTPStatus.OK
    assert str(relationship) == '{0} <--> {1} [{2}]'.format(
        str(patient),
        str(caregiver_dict['caregiver']),
        str(form_data['relationship_type']),
    )


@pytest.mark.django_db()
def test_create_new_relationship(registration_user: Client) -> None:
    """Test create a new relationship instance."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    patient_record = OIEPatientData(
        date_of_birth=date.fromisoformat('2014-05-09'),
        first_name='Lisa',
        last_name='Simpson',
        sex='F',
        alias='',
        deceased=True,
        death_date_time=datetime.strptime('2084-05-09 09:20:30', '%Y-%m-%d %H:%M:%S'),
        ramq='LISA99991313',
        ramq_expiration=datetime.strptime('2044-01-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MCH',
                mrn='9999994',
                active=True,
            ),
            OIEMRNData(
                site='RVH',
                mrn='9999993',
                active=True,
            ),
        ],
    )
    form_data = {
        'user_type': '0',
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'patient_record': patient_record,
        'relationship_type': factories.RelationshipType(name='Parent or Guardian'),
    }

    caregiver_user = Caregiver(first_name=form_data['first_name'], last_name=form_data['last_name'])
    caregiver = factories.CaregiverProfile(user_id=caregiver_user.id)

    caregiver_dict = instance._create_caregiver_profile(
        form_data=form_data,
        random_username_length=constants.USERNAME_LENGTH,
    )

    patient = instance._create_patient(form_data=form_data)

    factories.Relationship(type=form_data['relationship_type'], caregiver=caregiver, patient=patient)

    relationship = instance._create_relationship(
        form_data=form_data,
        caregiver_dict=caregiver_dict,
        patient=patient,
    )

    assert response.status_code == HTTPStatus.OK
    assert str(relationship) == '{0} <--> {1} [{2}]'.format(
        str(patient),
        str(caregiver_dict['caregiver']),
        str(form_data['relationship_type']),
    )


@pytest.mark.django_db()
def test_process_form_data(registration_user: Client) -> None:
    """Test process the list form data and then return a dictionay form data."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    form_data = [
        {
            'medical_card': constants.MedicalCard.MRN.name,
            'medical_number': '4356789',
            'site_code': 'MGH',
        },
        {
            'user_email': 'marge.simpson@gmail.com',
            'user_phone': '+15141111111',
        },
        {
            'relationship_type': factories.RelationshipType(name='self'),
            'requestor_form': False,
        },
    ]

    processed_form_data = {
        'medical_card': constants.MedicalCard.MRN.name,
        'medical_number': '4356789',
        'site_code': 'MGH',
        'user_email': 'marge.simpson@gmail.com',
        'user_phone': '+15141111111',
        'relationship_type': factories.RelationshipType(name='self'),
        'requestor_form': False,
    }

    assert response.status_code == HTTPStatus.OK
    assert instance._process_form_data(form_data) == processed_form_data


@pytest.mark.django_db()
def test_qr_code_class_type(registration_user: Client) -> None:
    """Test QR-code image stream class type."""
    request = _init_session(registration_user)

    test_view = _TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert isinstance(instance._generate_qr_code('Wcyxh2Ucwu'), io.BytesIO)


def test_error_message_mrn_with_same_site_code() -> None:
    """Test error message shows up once some MRN records having the same site code."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(
        mrns=[
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MGH',
                mrn='9999994',
                active=True,
            ),
            OIEMRNData(
                site='MGH',
                mrn='9999993',
                active=True,
            ),
        ],
    )
    assert AccessRequestView()._update_patient_confirmation_context(
        {},
        patient_data,
    )['error_message'] == 'Please note multiple MRNs need to be merged by medical records.'


def test_error_message_searched_patient_deceased() -> None:
    """Test error message shows up once searched patient is deceased."""
    patient_data = CUSTOMIZED_OIE_PATIENT_DATA._replace(deceased=True)

    error_message = ('Unable to complete action with this patient. Please contact Medical Records.')
    assert AccessRequestView()._update_patient_confirmation_context(
        {},
        patient_data,
    )['error_message'] == error_message


def test_relationships_list_table(relationship_user: Client) -> None:
    """Ensures Relationships list uses the corresponding table."""
    factories.Relationship(status=models.RelationshipStatus.PENDING)

    response = relationship_user.get(reverse('patients:relationships-list'))

    assert response.context['table'].__class__ == tables.PendingRelationshipTable


def test_relationships_list_empty(relationship_user: Client) -> None:
    """Ensures Relationships list shows message when no types are defined."""
    response = relationship_user.get(reverse('patients:relationships-list'))

    assert response.status_code == HTTPStatus.OK

    assertContains(response, 'No caregiver requests found.')


def test_relationships_pending_list(relationship_user: Client) -> None:
    """Ensures Relationships with pending status are listed."""
    caregivertype2 = factories.RelationshipType(name='caregiver_2')
    caregivertype3 = factories.RelationshipType(name='caregiver_3')
    relationships = [
        factories.Relationship(type=caregivertype2, request_date='2017-01-01'),
        factories.Relationship(type=caregivertype3, request_date='2016-01-01'),
    ]

    response = relationship_user.get(reverse('patients:relationships-list'))
    response.content.decode('utf-8')

    assertQuerysetEqual(list(reversed(response.context['relationship_list'])), relationships)

    for relationship in relationships:
        assertContains(response, f'<td >{relationship.type.name}</td>')  # noqa: WPS237


def test_relationships_not_pending_not_list(relationship_user: Client) -> None:
    """Ensures that only Relationships with pending status are listed."""
    caregivertype1 = factories.RelationshipType(name='caregiver_1')
    caregivertype2 = factories.RelationshipType(name='caregiver_2')
    caregivertype3 = factories.RelationshipType(name='caregiver_3')
    factories.Relationship(status=models.RelationshipStatus.CONFIRMED, type=caregivertype1)
    factories.Relationship(type=caregivertype2)
    factories.Relationship(type=caregivertype3)

    response = relationship_user.get(reverse('patients:relationships-list'))

    assert len(response.context['relationship_list']) == 2


def test_relationships_pending_list_table(relationship_user: Client) -> None:
    """Ensures that pending relationships list uses the corresponding table."""
    response = relationship_user.get(reverse('patients:relationships-list'))

    assert response.context['table'].__class__ == tables.PendingRelationshipTable


def test_form_pending_update_urls(relationship_user: Client) -> None:
    """Ensure that the correct cancel url and success url are provided in the response."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver)
    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    assert response.context['cancel_url'] == reverse('patients:relationships-list')
    assert response.context['view'].get_success_url() == reverse('patients:relationships-list')


def test_form_pending_readonly_update_template(relationship_user: Client) -> None:
    """Ensure that the correct html template appears in update and readonly requests."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    hospital_patient = factories.HospitalPatient()
    caregiver = factories.CaregiverProfile()
    relationship_record = factories.Relationship(
        pk=1,
        patient=hospital_patient.patient,
        type=relationshiptype,
        caregiver=caregiver,
        status=models.RelationshipStatus.EXPIRED,
    )

    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    # test in case of EXPIRED status, readonly view
    assertContains(response, '<p>{0}</p>'.format(str(relationship_record.patient)))
    assertContains(response, '{0}: {1}'.format(hospital_patient.site.code, hospital_patient.mrn))
    assertContains(response, 'Back')
    assertNotContains(response, 'Save')

    relationship_record = factories.Relationship(
        pk=2,
        patient=hospital_patient.patient,
        type=relationshiptype,
        caregiver=caregiver,
        status=models.RelationshipStatus.PENDING,
    )

    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 2}))

    # test in case of PENDING status, update view
    assertContains(response, str(relationship_record.patient.first_name))
    assertContains(response, 'name="first_name"')
    assertContains(response, 'Cancel')
    assertContains(response, 'Save')


# Search Patient Access Results tests
@pytest.mark.parametrize(
    'status', [
        models.RelationshipStatus.PENDING,
        models.RelationshipStatus.CONFIRMED,
        models.RelationshipStatus.REVOKED,
        models.RelationshipStatus.DENIED,
    ],
)
def test_relationships_search_result_form(relationship_user: Client, status: models.RelationshipStatus) -> None:
    """Ensures that edit search results uses the right form for each all relationship statuses."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    factories.Relationship(pk=1, type=relationshiptype, status=status)
    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    assert response.context['form'].__class__ == forms.RelationshipAccessForm


def test_relationships_search_result_content(relationship_user: Client) -> None:
    """Ensures that search relationships result passed info is correct."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver)
    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    assert response.context['relationship'] == relationship


def test_form_search_result_update(relationship_user: Client) -> None:
    """Ensures that the form can update a record in search result."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver, status=models.RelationshipStatus.PENDING)
    response_get = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    # assert getter
    assert response_get.status_code == HTTPStatus.OK

    # prepare data to post
    data = model_to_dict(response_get.context_data['object'])  # type: ignore[attr-defined]
    data['status'] = models.RelationshipStatus.CONFIRMED
    data['first_name'] = 'test_firstname'
    data['last_name'] = 'test_lastname'
    data['cancel_url'] = response_get.context_data['cancel_url']  # type: ignore[attr-defined]

    # post
    relationship_user.post(reverse('patients:relationships-view-update', kwargs={'pk': 1}), data=data)

    # assert successful update
    relationship_record = models.Relationship.objects.get(pk=1)
    assert relationship_record.status == models.RelationshipStatus.CONFIRMED


def test_form_search_result_update_view(relationship_user: Client) -> None:
    """Ensures that the correct view and form are used in search result."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver, status=models.RelationshipStatus.PENDING)
    response_get = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    assert response_get.context_data['form'].__class__ == forms.RelationshipAccessForm  # type: ignore[attr-defined]
    assert response_get.context_data['view'].__class__ == ManageCaregiverAccessUpdateView  # type: ignore[attr-defined]


def test_form_search_result_default_sucess_url(relationship_user: Client) -> None:
    """Ensures that the correct cancel url and success url are provided in the response."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver, status=models.RelationshipStatus.PENDING)
    response_get = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    assert response_get.context_data['view'].get_context_data()['cancel_url'] == reverse(  # type: ignore[attr-defined]
        'patients:relationships-list',
    )
    assert response_get.context_data['view'].get_success_url() == reverse(  # type: ignore[attr-defined]
        'patients:relationships-list',
    )


def test_form_search_result_http_referer(relationship_user: Client) -> None:
    """Ensures that the correct cancel url and success url are provided in the response."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver, status=models.RelationshipStatus.PENDING)
    response_get = relationship_user.get(
        reverse(
            'patients:relationships-view-update',
            kwargs={'pk': 1},
        ),
        HTTP_REFERER='patient/test/?search-query',
    )

    # assert cancel_url being set when HTTP_REFERER is not empty
    cancel_url = response_get.context_data['view'].get_context_data()['cancel_url']  # type: ignore[attr-defined]
    assert cancel_url == 'patient/test/?search-query'

    response_post = relationship_user.post(
        reverse(
            'patients:relationships-view-update',
            kwargs={'pk': 1},
        ),
        {
            'cancel_url': cancel_url,
            'first_name': 'test_firstname',
            'last_name': 'test_lastname',
        },
    )

    # assert success_url is equal to the new cancel_url
    success_url = response_post.context_data['view'].get_success_url()  # type: ignore[attr-defined]
    assert success_url == cancel_url


@pytest.mark.parametrize(
    'role_type', [
        models.RoleType.SELF,
        models.RoleType.MANDATARY,
        models.RoleType.PARENT_GUARDIAN,
        models.RoleType.GUARDIAN_CAREGIVER,
    ],
)
def test_valid_relationship_contain_role_type_being_updated(
    relationship_user: Client,
    role_type: models.RoleType,
) -> None:
    """Ensure to include type being updated in the valid types list."""
    relationshiptype = factories.RelationshipType(role_type=role_type, name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver)
    response_get = relationship_user.get(
        reverse(
            'patients:relationships-view-update',
            kwargs={'pk': 1},
        ),
        HTTP_REFERER='patient/test/?search-query',
    )

    # get choices available in the initialized form
    response_context = response_get.context['form']
    type_choices = response_context.fields['type'].queryset

    # assert the relationship of relationshiptype being edited is in the choices of the type field in the form
    assert relationshiptype in type_choices


def test_form_readonly_pendingrelationship_cannot_update(relationship_user: Client) -> None:
    """Ensures that post is not allowed for readonly pending even if front-end is bypassed."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship(
        pk=1,
        type=relationshiptype,
        caregiver=caregiver,
        status=models.RelationshipStatus.EXPIRED,
    )
    response_get = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    # assert getter
    assert response_get.status_code == HTTPStatus.OK

    # prepare data to post
    data = model_to_dict(relationship)
    data['status'] = models.RelationshipStatus.CONFIRMED
    data['first_name'] = 'test_firstname'
    data['last_name'] = 'test_lastname'
    data['cancel_url'] = response_get.context['cancel_url']

    # post
    response_post = relationship_user.post(
        reverse('patients:relationships-view-update', kwargs={'pk': 1}),
        data=data,
    )

    # make sure that update is not applied and response is `NOT_ALLOWED`
    assert response_post.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    relationship_object = models.Relationship.objects.get(pk=1)
    new_caregiver = relationship_object.caregiver.user
    assert new_caregiver.first_name != 'test_firstname'


def test_relationship_cannot_update_invalid_entry(relationship_user: Client) -> None:
    """Ensures that post is not allowed for wrong last_name and correct error message is shown."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship(
        pk=1,
        type=relationshiptype,
        caregiver=caregiver,
        status=models.RelationshipStatus.PENDING,
    )
    response_get = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    # assert getter
    assert response_get.status_code == HTTPStatus.OK

    # prepare data to post
    longname = ''.join('a' for letter in range(200))
    error_message = 'Ensure this value has at most 150 characters (it has 200).'

    data = model_to_dict(relationship)
    data['status'] = models.RelationshipStatus.CONFIRMED
    data['first_name'] = 'test_firstname'
    data['last_name'] = longname
    data['cancel_url'] = response_get.context['cancel_url']

    # post
    response_post = relationship_user.post(
        reverse('patients:relationships-view-update', kwargs={'pk': 1}),
        data=data,
    )

    form = response_post.context['form']
    assert not form.is_valid()
    assert form.errors['last_name'][0] == error_message


def test_relationship_update_success(relationship_user: Client) -> None:
    """Ensures that post is successful for correct entries."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship(
        pk=1,
        type=relationshiptype,
        caregiver=caregiver,
        status=models.RelationshipStatus.PENDING,
    )
    response_get = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    # assert getter
    assert response_get.status_code == HTTPStatus.OK

    # prepare data to post
    data = model_to_dict(relationship)
    data['status'] = models.RelationshipStatus.CONFIRMED
    data['first_name'] = 'test_firstname'
    data['last_name'] = 'test_lastname'
    data['cancel_url'] = response_get.context['cancel_url']

    # post
    relationship_user.post(
        reverse('patients:relationships-view-update', kwargs={'pk': 1}),
        data=data,
    )

    # assertions
    relationship_record = models.Relationship.objects.get(pk=1)
    assert relationship_record.caregiver.user.last_name == data['last_name']


# relationshiptype tests
def test_relationshiptype_list_delete_unavailable(relationshiptype_user: Client) -> None:
    """Ensure the delete button does not appear, but update does, in the special rendering for restricted role types."""
    response = relationshiptype_user.get(reverse('patients:relationshiptype-list'))

    soup = BeautifulSoup(response.content, 'html.parser')
    delete_button_data = soup.find_all('a', href=re.compile('delete'))
    update_button_data = soup.find_all('a', href=re.compile('update'))

    assert response.status_code == HTTPStatus.OK
    assert not delete_button_data
    assert update_button_data


def test_relationshiptype_list_delete_available(relationshiptype_user: Client) -> None:
    """Ensure the delete and update buttons do appear for regular relationship types."""
    new_relationship_type = factories.RelationshipType()
    relationshiptype_user.post(
        reverse('patients:relationshiptype-create'),
        data=model_to_dict(new_relationship_type, exclude=['id', 'end_age']),
    )

    response = relationshiptype_user.get(reverse('patients:relationshiptype-list'))

    soup = BeautifulSoup(response.content, 'html.parser')
    delete_button_data = soup.find_all('a', href=re.compile('delete'))
    update_button_data = soup.find_all('a', href=re.compile('update'))

    assert response.status_code == HTTPStatus.OK
    assert delete_button_data
    assert update_button_data


def test_relationships_pending_form(relationship_user: Client) -> None:
    """Ensures that pending relationships edit uses the right form."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    factories.Relationship(pk=1, type=relationshiptype)
    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    assert response.context['form'].__class__ == forms.RelationshipAccessForm


def test_relationships_pending_form_content(relationship_user: Client) -> None:
    """Ensures that pending relationships passed info is correct."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver)
    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))

    assert response.context['relationship'] == relationship


def test_relationships_pending_form_response(relationship_user: Client) -> None:
    """Ensures that pending relationships displayed info is correct."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    patient = factories.Patient()
    relationship = factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver, patient=patient)
    response = relationship_user.get(reverse('patients:relationships-view-update', kwargs={'pk': 1}))
    response.content.decode('utf-8')

    assertContains(response, patient)
    assertContains(response, relationship.caregiver.user.first_name)
    assertContains(response, relationship.caregiver.user.last_name)
    assertContains(response, relationship.patient.ramq)


@pytest.mark.parametrize(
    'url_name', [
        reverse('patients:relationships-list'),
        reverse('patients:relationships-view-update', args=(1,)),
    ],
)
def test_relationship_permission_required_fail(user_client: Client, django_user_model: User, url_name: str) -> None:
    """Ensure that `Relationship` permission denied error is raised when not having privilege."""
    user = django_user_model.objects.create(username='test_relationship_user')
    factories.Relationship(pk=1)
    user_client.force_login(user)
    response = user_client.get(url_name)
    request = RequestFactory().get(response)  # type: ignore[arg-type]
    request.user = user
    with pytest.raises(PermissionDenied):
        ManageCaregiverAccessListView.as_view()(request)


@pytest.mark.parametrize(
    'url_name', [
        reverse('patients:relationships-list'),
        reverse('patients:relationships-view-update', args=(1,)),
    ],
)
def test_relationship_permission_required_success(user_client: Client, django_user_model: User, url_name: str) -> None:
    """Ensure that `Relationship` can be accessed with the required permission."""
    user = django_user_model.objects.create(username='test_relationship_user')
    user_client.force_login(user)
    permission = Permission.objects.get(codename='can_manage_relationships')
    user.user_permissions.add(permission)
    factories.Relationship(pk=1)

    response = user_client.get(url_name)

    assert response.status_code == HTTPStatus.OK


def test_relationships_response_contains_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that pending relationships is displayed for users with permission."""
    user = django_user_model.objects.create(username='test_relationship_user')
    user_client.force_login(user)
    permission = Permission.objects.get(codename='can_manage_relationships')
    user.user_permissions.add(permission)

    response = user_client.get(reverse('hospital-settings:index'))

    assertContains(response, 'Manage Caregiver Access')


def test_relationships_pending_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that pending relationships is not displayed for users without permission."""
    user = django_user_model.objects.create(username='test_relationship_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    assertNotContains(response, 'Pending Requests')


# can manage relationshiptype permissions


@pytest.mark.parametrize(
    'url_name', [
        reverse('patients:relationshiptype-list'),
        reverse('patients:relationshiptype-create'),
        reverse('patients:relationshiptype-update', args=(11,)),
        reverse('patients:relationshiptype-delete', args=(11,)),
    ],
)
def test_relationshiptype_perm_required_fail(user_client: Client, django_user_model: User, url_name: str) -> None:
    """Ensure that `RelationshipType` permission denied error is raised when not having privilege."""
    user = django_user_model.objects.create(username='test_relationshiptype_user')
    factories.RelationshipType(pk=11)
    user_client.force_login(user)

    response = user_client.get(url_name)
    request = RequestFactory().get(response)  # type: ignore[arg-type]

    request.user = user
    with pytest.raises(PermissionDenied):
        ManageCaregiverAccessListView.as_view()(request)


@pytest.mark.parametrize(
    'url_name', [
        reverse('patients:relationshiptype-list'),
        reverse('patients:relationshiptype-create'),
        reverse('patients:relationshiptype-update', args=(11,)),
        reverse('patients:relationshiptype-delete', args=(11,)),
    ],
)
def test_relationshiptype_perm_required_success(
    relationshiptype_user: Client,
    django_user_model: User,
    url_name: str,
) -> None:
    """Ensure that `RelationshipType` can be accessed with the required permission."""
    factories.RelationshipType(pk=11)

    response = relationshiptype_user.get(url_name)

    assert response.status_code == HTTPStatus.OK


def test_relationshiptype_response_contains_menu(relationshiptype_user: Client, django_user_model: User) -> None:
    """Ensures that pending relationshiptypes is displayed for users with permission."""
    response = relationshiptype_user.get(reverse('hospital-settings:index'))

    assertContains(response, 'Relationship Types')


def test_relationshiptype_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that pending relationshiptypes is not displayed for users without permission."""
    user = django_user_model.objects.create(username='test_relationshiptype_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    assertNotContains(response, 'Relationship Types')


# can perform registration permissions


def test_registration_permission_required_success(registration_user: Client) -> None:
    """Ensure that registration can be performed with the required permission."""
    response = registration_user.get(reverse('patients:access-request'))

    assert response.status_code == HTTPStatus.OK


def test_registration_permission_required_fail(user_client: Client, django_user_model: User) -> None:
    """Ensure that registration permission denied error is raised when not having privilege."""
    user = django_user_model.objects.create(username='test_registration_user')
    user_client.force_login(user)

    response = user_client.get(reverse('patients:access-request'))
    request = RequestFactory().get(response)  # type: ignore[arg-type]

    request.user = user
    with pytest.raises(PermissionDenied):
        AccessRequestView.as_view()(request)


def test_registration_response_contains_menu(registration_user: Client) -> None:
    """Ensures that Opal Registration is displayed for users with permission."""
    response = registration_user.get(reverse('patients:access-request'))

    assertContains(response, 'Opal Registration')


def test_registration_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that Opal Registration is not displayed for users without permission."""
    user = django_user_model.objects.create(username='test_registration_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    assertNotContains(response, 'Opal Registration')


def test_caregiver_access_tables_displayed_by_mrn(relationship_user: Client, django_user_model: User) -> None:
    """
    Ensure that `Search Patient Access` template displays `Patient Details` table and `Caregiver Details` table.

    The search is performed by using MRN number.
    """
    hospital_patient = factories.HospitalPatient()
    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.self_type(),
    )
    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.guardian_caregiver(),
    )
    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.mandatary(),
    )
    factories.Relationship(
        patient=factories.Patient(ramq='TEST123'),
        type=models.RelationshipType.objects.parent_guardian(),
    )

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': hospital_patient.mrn,
    }
    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-list'),
        QUERY_STRING=query_string,
    )

    # Check 'medical_number' field name
    mrn_filter = response.context['filter']

    # Check filter's queryset
    assertQuerysetEqual(
        mrn_filter.qs,
        models.Relationship.objects.filter(patient__hospital_patients__mrn=hospital_patient.mrn),
        ordered=False,
    )

    # Check number of tables
    soup = BeautifulSoup(response.content, 'html.parser')
    search_tables = soup.find_all('tbody')
    assert len(search_tables) == 1

    # Check how many patients are displayed
    patients = search_tables[0].find_all('tr')
    assert len(patients) == 3


def test_not_display_duplicated_patients(relationship_user: Client, django_user_model: User) -> None:
    """
    Ensure that `Search Patient Access` template does not display duplicated `Patient Details` search results.

    The search is performed by using MRN number and Site name.
    """
    patient1 = factories.Patient(first_name='aaa', ramq='OTES01161973')
    patient2 = factories.Patient(first_name='bbb', ramq='OTES01161972')

    site1 = factories.Site(name='MCH')
    site2 = factories.Site(name='RVH')

    hospital_patient1 = factories.HospitalPatient(mrn='9999991', site=site1, patient=patient1)
    factories.HospitalPatient(mrn='9999992', site=site2, patient=patient1)
    factories.HospitalPatient(mrn='9999991', site=site2, patient=patient2)

    user = Caregiver()
    caregiver_profile = factories.CaregiverProfile(user=user)
    factories.Relationship(
        caregiver=caregiver_profile,
        patient=patient1,
        type=models.RelationshipType.objects.self_type(),
    )
    factories.Relationship(
        caregiver=caregiver_profile,
        patient=patient2,
        type=models.RelationshipType.objects.guardian_caregiver(),
    )

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': site2.id,
        'medical_number': hospital_patient1.mrn,
    }
    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-list'),
        QUERY_STRING=query_string,
    )

    # get filter
    mrn_filter = response.context['filter']

    # Check filter's queryset
    assertQuerysetEqual(
        mrn_filter.qs,
        models.Relationship.objects.filter(
            patient__hospital_patients__mrn=hospital_patient1.mrn,
            patient__hospital_patients__site=site2,
        ),
        ordered=False,
    )

    # Check number of tables
    soup = BeautifulSoup(response.content, 'html.parser')
    search_tables = soup.find_all('tbody')
    assert len(search_tables) == 1

    # Check how many patients are displayed, should be one
    # To confirm there is no duplicated patients
    patients = search_tables[0].find_all('tr')
    assert len(patients) == 1

    # Assert patient name to make sure the search result is patient2
    patient_names = patients[0].find_all('td')
    assert strip_tags(patient_names[0]) == str(patient2)


def test_caregiver_access_tables_displayed_by_ramq(relationship_user: Client, django_user_model: User) -> None:
    """
    Ensure that `Search Patient Access` template displays `Patient Details` table and `Caregiver Details` table.

    The search is performed by using RAMQ number.
    """
    hospital_patient = factories.HospitalPatient(
        patient=factories.Patient(ramq='OTES01161973'),
    )
    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.self_type(),
    )
    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.mandatary(),
    )
    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.parent_guardian(),
    )
    factories.Relationship(
        patient=factories.Patient(ramq='TEST123'),
        type=factories.RelationshipType(),
    )

    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
        'medical_number': hospital_patient.patient.ramq,
    }
    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-list'),
        QUERY_STRING=query_string,
    )
    response.content.decode('utf-8')
    assert response.status_code == HTTPStatus.OK

    # Check 'medical_number' field name
    ramq_filter = response.context['filter']

    # Check filter's queryset
    assertQuerysetEqual(
        ramq_filter.qs,
        models.Relationship.objects.filter(patient__ramq=hospital_patient.patient.ramq),
        ordered=False,
    )

    # Check number of tables
    soup = BeautifulSoup(response.content, 'html.parser')
    search_tables = soup.find_all('tbody')
    assert len(search_tables) == 1

    # Check how many patients/caregivers are displayed
    patients = search_tables[0].find_all('tr')
    assert len(patients) == 3


# Access Request Tests
def test_access_request_cancel_button(registration_user: Client) -> None:
    """Ensure the cancel button links to the correct URL."""
    url = reverse('patients:access-request-new')
    response = registration_user.get(url)

    assertContains(response, f'href="{url}"')


def test_access_request_initial_search(registration_user: Client) -> None:
    """Ensure that the patient search form initializes fields values as expected."""
    site = factories.Site()

    # initialize the session storage
    response = registration_user.get(reverse('patients:access-request-new'))

    assert response.status_code == HTTPStatus.OK

    form_data = {
        'current_step': 'search',
        'search-card_type': constants.MedicalCard.MRN.name,
        'search-medical_number': '',
    }

    response_post = registration_user.post(reverse('patients:access-request-new'), data=form_data)

    # assert site field is being initialized with site when there is only one site
    context = response_post.context
    assert context['current_forms'][0]['site'].initial == site
