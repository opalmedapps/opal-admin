from http import HTTPStatus
from typing import Any, Tuple

from django.contrib.sessions.middleware import SessionMiddleware
from django.forms.models import model_to_dict
from django.http import HttpRequest
from django.test import Client, RequestFactory
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertQuerysetEqual, assertTemplateUsed

from opal.hospital_settings.models import Site

from .. import factories, forms, models, tables, views


def test_relationshiptypes_list_table(user_client: Client) -> None:
    """Relationship types list uses the corresponding table."""
    response = user_client.get(reverse('patients:relationshiptype-list'))

    assert response.context['table'].__class__ == tables.RelationshipTypeTable


def test_relationshiptypes_list_empty(user_client: Client) -> None:
    """Relationship types list shows message when no types are defined."""
    response = user_client.get(reverse('patients:relationshiptype-list'))

    assert response.status_code == HTTPStatus.OK

    assertContains(response, 'No relationship types defined.')


def test_relationshiptypes_list(user_client: Client) -> None:
    """Relationship types are listed."""
    types = [factories.RelationshipType(), factories.RelationshipType(name='Second')]

    response = user_client.get(reverse('patients:relationshiptype-list'))
    content = response.content.decode('utf-8')
    print(content)

    assertQuerysetEqual(response.context['relationshiptype_list'], types)

    for relationship_type in types:
        assertContains(response, f'<td >{relationship_type.name}</td>')


def test_relationshiptype_create_get(user_client: Client) -> None:
    """A new relationship type can be created in a form."""
    response = user_client.get(reverse('patients:relationshiptype-create'))

    assertContains(response, 'Create Relationship Type')


def test_relationshiptype_create(user_client: Client) -> None:
    """A new relationship type can be created."""
    relationship_type = factories.RelationshipType.build(name='Testname')

    user_client.post(
        reverse('patients:relationshiptype-create'),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )

    assert models.RelationshipType.objects.count() == 1
    assert models.RelationshipType.objects.get().name == relationship_type.name


def test_relationshiptype_update_get(user_client: Client) -> None:
    """An existing relationship type can be edited."""
    relationship_type = factories.RelationshipType()

    response = user_client.get(
        reverse('patients:relationshiptype-update', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )

    assertContains(response, 'Update Relationship Type')
    assertContains(response, 'value="Self"')


def test_relationshiptype_update_post(user_client: Client) -> None:
    """An existing relationship type can be updated."""
    relationship_type = factories.RelationshipType()

    relationship_type.end_age = 100

    user_client.post(
        reverse('patients:relationshiptype-update', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id']),
    )

    assert models.RelationshipType.objects.get().end_age == 100


def test_relationshiptype_delete_get(user_client: Client) -> None:
    """Deleting a relationship type needs to be confirmed."""
    relationship_type = factories.RelationshipType()

    response = user_client.get(
        reverse('patients:relationshiptype-delete', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )

    assertContains(response, 'Are you sure you want to delete the following relationship type: Self?')


def test_relationshiptype_delete(user_client: Client) -> None:
    """An existing relationship type can be deleted."""
    relationship_type = factories.RelationshipType()

    user_client.delete(
        reverse('patients:relationshiptype-delete', kwargs={'pk': relationship_type.pk}),
    )

    assert models.RelationshipType.objects.count() == 0


# tuple with patients wizard form templates and corresponding url names
test_patient_multiform_url_template_data: list[Tuple] = [
    ('patients:access-request', 'patients/access_request/access_request.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_initial_call(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that steps are called initially."""
    url = reverse(url_name)
    response = user_client.get(url)
    wizard = response.context['wizard']

    assert response.status_code == HTTPStatus.OK
    assert wizard['steps'].current == 'site'
    assert wizard['steps'].last == 'confirm'
    assert wizard['steps'].next == 'search'
    assert wizard['steps'].count == 3


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_post_error(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the validation error happens with the form if the field is missing value."""
    url = reverse(url_name)
    step_one_data = {
        'access_request_view-current_step': 'site',
    }
    response = user_client.post(url, step_one_data)

    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'
    assert response.context['wizard']['form'].errors == {'sites': ['This field is required.']}


def _wizard_step_data(site: Site) -> Tuple[dict, dict, dict]:
    return (
        {
            'site-sites': site.pk,
            'access_request_view-current_step': 'site',
        },
        {
            'search-medical_card': 'mrn',
            'search-medical_number': '99996',
            'access_request_view-current_step': 'search',
        },
        {
            'confirm-is_correct': True,
            'access_request_view-current_step': 'confirm',
        },
    )


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_post_mgmt_data_missing(
    user_client: Client,
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

    response = user_client.post(url, wizard_step_one_data)
    # view should return HTTP 400 Bad Request
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_post_success(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the form submission with POST is successful."""
    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    response = user_client.post(url, wizard_step_data[0])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'search'
    assert response.context['wizard']['steps'].step0 == 1
    assert response.context['wizard']['steps'].prev == 'site'
    assert response.context['wizard']['steps'].next == 'confirm'


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_stepback(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the form can go back to the previous step."""
    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'

    response = user_client.post(url, wizard_step_data[0])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'search'

    response = user_client.post(url, {
        'wizard_goto_step': response.context['wizard']['steps'].prev,
    })
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_form_finish(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that the form can go through all the steps."""
    url = reverse(url_name)
    wizard_step_data = _wizard_step_data(factories.Site())
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'

    response = user_client.post(url, wizard_step_data[0])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'search'

    response = user_client.post(url, wizard_step_data[1])
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'confirm'


def test_access_request_done_redirects_temp(user_client: Client) -> None:
    """Ensure that when the page is submitted it redirects to the final page."""
    url = reverse('patients:access-request')
    site = factories.Site()
    form_data = [
        ('site', {'sites': site.pk}),
        ('search', {'medical_card': 'ramq', 'medical_number': 'RAMQ99996666'}),
        ('confirm', {'is_correct': True}),
    ]
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context['wizard']['steps'].current == 'site'

    for step, step_data in form_data:
        step_data = {
            '{0}-{1}'.format(step, key): value
            for key, value in step_data.items()
        }
        step_data['access_request_view-current_step'] = step
        response = user_client.post(url, step_data, follow=True)
        assert response.status_code == HTTPStatus.OK

        if 'site' in step:
            assert response.context['wizard']['steps'].current == 'search'
        elif 'search' in step:
            assert response.context['wizard']['steps'].current == 'confirm'
        elif 'confirm' in step:
            assertTemplateUsed(response, 'patients/access_request/test_qr_code.html')


class TestAccessRequestView(views.AccessRequestView):
    """
    This view is to test AccessRequestView.

    It patches dispatch to return the view instance as well for testing.

    It requires since the WizardView needs to be fully set up.
    """

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Tuple[Any, 'TestAccessRequestView']:
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


def _init_session() -> HttpRequest:
    """
    Initialize the session.

    Returns:
        the request
    """
    request = RequestFactory().get('/')
    # adding session
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db()
def test_unexpected_step() -> None:
    """Test unexpected step 'search'."""
    request = _init_session()

    test_view = TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('search') == {}  # noqa: WPS520


@pytest.mark.django_db()
def test_expected_step_without_session_storage() -> None:
    """Test expected step 'site' without session storage of saving user selection."""
    request = _init_session()

    test_view = TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('site') == {}  # noqa: WPS520


@pytest.mark.django_db()
def test_expected_step_with_valid_id_in_session() -> None:
    """Test expected step 'site' with session storage of saving user selection."""
    request = _init_session()
    request.session['site_selection'] = 2
    # adding Site records
    factories.Site(pk=1)
    factories.Site(pk=2)

    test_view = TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('site') == {
        'sites': Site.objects.filter(pk=2).first(),
    }


@pytest.mark.django_db()
def test_expected_step_with_invalid_id_in_session() -> None:
    """Test expected step 'site' with session storage of saving user selection."""
    request = _init_session()
    request.session['site_selection'] = 3
    # adding Site records
    factories.Site(pk=1)
    factories.Site(pk=2)

    test_view = TestAccessRequestView.as_view()
    response, instance = test_view(request)

    assert response.status_code == HTTPStatus.OK
    assert instance.get_form_initial('site') == {}  # noqa: WPS520


@pytest.mark.django_db()
def test_process_step_select_site_form() -> None:
    """Test expected form 'SelectSiteForm'."""
    request = _init_session()

    test_view = TestAccessRequestView.as_view()
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


@pytest.mark.django_db()
def test_some_mrns_have_same_site_code() -> None:
    """Test some MRN records have the same site code."""
    patient_mrn_records = {
        'mrns': [
            {
                'site': 'MGH',
                'mrn': '9999993',
                'active': True,
            },
            {
                'site': 'MGH',
                'mrn': '9999994',
                'active': True,
            },
            {
                'site': 'RVH',
                'mrn': '9999993',
                'active': True,
            },
        ],
    }
    assert views.AccessRequestView()._has_multiple_mrns_with_same_site_code(patient_mrn_records) is True


@pytest.mark.django_db()
def test_all_mrns_have_same_site_code() -> None:
    """Test all MRN records have the same site code."""
    patient_mrn_records = {
        'mrns': [
            {
                'site': 'MGH',
                'mrn': '9999993',
                'active': True,
            },
            {
                'site': 'MGH',
                'mrn': '9999994',
                'active': True,
            },
            {
                'site': 'MGH',
                'mrn': '9999993',
                'active': True,
            },
        ],
    }
    assert views.AccessRequestView()._has_multiple_mrns_with_same_site_code(patient_mrn_records) is True


@pytest.mark.django_db()
def test_no_mrns_have_same_site_code() -> None:
    """Test No MRN records have the same site code."""
    patient_mrn_records = {
        'mrns': [
            {
                'site': 'MGH',
                'mrn': '9999993',
                'active': True,
            },
            {
                'site': 'MCH',
                'mrn': '9999994',
                'active': True,
            },
            {
                'site': 'RVH',
                'mrn': '9999993',
                'active': True,
            },
        ],
    }
    assert views.AccessRequestView()._has_multiple_mrns_with_same_site_code(patient_mrn_records) is False
