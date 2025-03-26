import re
import urllib
from datetime import date, datetime
from http import HTTPStatus
from typing import Tuple

from django.contrib.auth.models import AbstractUser, Permission
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils.html import strip_tags

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains, assertNotContains, assertQuerysetEqual, assertTemplateUsed

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
    relationshiptype = factories.RelationshipType(pk=11, name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver)
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

    relationship_data = model_to_dict(relationship)
    relationship_data['type'] = 11
    relationship_data['first_name'] = 'test_firstname'
    relationship_data['last_name'] = 'test_lastname'
    relationship_data['cancel_url'] = cancel_url

    response_post = relationship_user.post(
        reverse(
            'patients:relationships-view-update',
            kwargs={'pk': 1},
        ),
        data=relationship_data,
    )

    # assert success_url is equal to the new cancel_url
    assert response_post.url == cancel_url  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    'role_type', [
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
def test_access_request_permission(client: Client, registration_user: User) -> None:
    """Ensure that the access request view can be viewed with the `can_perform_registration` permission."""
    client.force_login(registration_user)
    response = client.get(reverse('patients:access-request'))

    assert response.status_code == HTTPStatus.OK


def test_access_request_no_permission(django_user_model: User) -> None:
    """Ensure that the access request view can not be viewed without the `can_perform_registration` permission."""
    request = RequestFactory().get(reverse('patients:access-request'))
    request.user = django_user_model.objects.create(username='testuser')

    with pytest.raises(PermissionDenied):
        AccessRequestView.as_view()(request)


def test_access_request_menu_shown(client: Client, registration_user: User) -> None:
    """Ensures that Opal Registration is displayed for users with permission."""
    client.force_login(registration_user)
    response = client.get(reverse('start'), follow=True)

    assertContains(response, 'Opal Registration')


def test_access_request_menu_hidden(user_client: Client) -> None:
    """Ensures that Opal Registration is not displayed for users without permission."""
    response = user_client.get(reverse('start'), follow=True)

    assertNotContains(response, 'Opal Registration')


def test_access_request_cancel_button(client: Client, registration_user: User) -> None:
    """Ensure the cancel button links to the correct URL."""
    url = reverse('patients:access-request')
    client.force_login(registration_user)
    response = client.get(url)

    assertContains(response, f'href="{url}"')


def test_access_request_initial_search(client: Client, registration_user: User) -> None:
    """Ensure that the patient search form initializes fields values as expected."""
    site = factories.Site()
    client.force_login(registration_user)

    # initialize the session storage
    response = client.get(reverse('patients:access-request'))

    assert response.status_code == HTTPStatus.OK

    form_data = {
        'current_step': 'search',
        'search-card_type': constants.MedicalCard.MRN.name,
        'search-medical_number': '',
    }

    response_post = client.post(reverse('patients:access-request'), data=form_data)

    # assert site field is being initialized with site when there is only one site
    context = response_post.context
    assert context['current_forms'][0]['site'].initial == site
