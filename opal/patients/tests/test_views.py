import json
import re
import urllib
from collections import OrderedDict
from datetime import date, datetime
from http import HTTPStatus
from typing import Any

from django.contrib.auth.models import Permission
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied, SuspiciousOperation
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils.html import strip_tags

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains, assertNotContains, assertQuerysetEqual, assertTemplateUsed
from pytest_mock.plugin import MockerFixture

from opal.caregivers.models import RegistrationCode
from opal.hospital_settings import factories as hospital_factories
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData
from opal.users.models import Caregiver, User

from .. import constants, factories, forms, models, tables
from ..views import AccessRequestView, ManageCaregiverAccessListView, ManageCaregiverAccessUpdateView

pytestmark = pytest.mark.django_db

OIE_PATIENT_DATA = OIEPatientData(
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

test_url_template_data: list[tuple[str, str]] = [
    (reverse('patients:relationships-list'), 'patients/relationships/pending_relationship_list.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_patients_urls_exist(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page exists at each URL address."""
    response = admin_client.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_views_use_correct_template(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page uses appropriate templates."""
    response = admin_client.get(url)

    assertTemplateUsed(response, template)


def test_relationshiptypes_list_table(relationshiptype_user: Client) -> None:
    """Relationship types list uses the corresponding table."""
    response = relationshiptype_user.get(reverse('patients:relationshiptype-list'))

    assert response.context['table'].__class__ == tables.RelationshipTypeTable


def test_relationshiptypes_list(relationshiptype_user: Client) -> None:
    """Relationship types are listed."""
    types = [factories.RelationshipType(), factories.RelationshipType(name='Second')]

    response = relationshiptype_user.get(reverse('patients:relationshiptype-list'))

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
        factories.Relationship(type=caregivertype2, request_date=date.fromisoformat('2017-01-01')),
        factories.Relationship(type=caregivertype3, request_date=date.fromisoformat('2016-01-01')),
    ]

    response = relationship_user.get(reverse('patients:relationships-list'))

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
    # the table shows the correct patient
    table: tables.PatientTable = response.context['table']

    assert table.data.data[0] == relationship_record.patient
    assertContains(response, '{0}: {1}'.format(hospital_patient.site.acronym, hospital_patient.mrn))
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


def test_form_search_result_default_success_url(relationship_user: Client) -> None:
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


def test_form_search_result_http_referrer(relationship_user: Client) -> None:
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


def test_caregiver_access_update_form_fail(relationship_user: Client) -> None:
    """Ensures patient cannot have different name from caregiver in self-relationship."""
    patient = factories.Patient()
    self_type = factories.RelationshipType(role_type=models.RoleType.SELF.name)
    relationship = factories.Relationship(patient=patient, type=self_type, status=models.RelationshipStatus.CONFIRMED)

    cancel_url = 'patient/test/?search-query'
    form_data = model_to_dict(relationship)
    form_data['pk'] = relationship.pk
    form_data['type'] = relationship.type.pk
    form_data['first_name'] = 'test_firstname'
    form_data['last_name'] = 'test_lastname'
    form_data['end_date'] = date.fromisoformat('2023-05-09')
    form_data['cancel_url'] = cancel_url

    url = reverse('patients:relationships-view-update', kwargs={'pk': relationship.pk})

    response_post = relationship_user.post(path=url, data=form_data)
    err_msg = 'A self-relationship was selected but the caregiver appears to be someone other than the patient.'
    assert err_msg in response_post.context['form'].errors['__all__']


@pytest.mark.parametrize(
    'role_type', [
        models.RoleType.MANDATARY,
        models.RoleType.PARENT_GUARDIAN,
        models.RoleType.GUARDIAN_CAREGIVER,
    ],
)
def test_caregiver_access_update_form_pass(relationship_user: Client, role_type: models.RoleType) -> None:
    """Ensure patient can have different name from caregiver in non-self relationship."""
    patient = factories.Patient()
    relationshiptype = factories.RelationshipType(role_type=role_type)
    relationship = factories.Relationship(patient=patient, type=relationshiptype)

    cancel_url = 'patient/test/?search-query'
    form_data = model_to_dict(relationship)
    form_data['pk'] = relationship.pk
    form_data['type'] = relationship.type.pk
    form_data['first_name'] = 'test_firstname'
    form_data['last_name'] = 'test_lastname'
    form_data['end_date'] = date.fromisoformat('2023-05-09')
    form_data['cancel_url'] = cancel_url

    url = reverse('patients:relationships-view-update', kwargs={'pk': relationship.pk})

    relationship_user.post(
        path=url,
        data=form_data,
    )

    relationship_record = models.Relationship.objects.get(pk=relationship.pk)
    # assert the first and last name have been changed
    assert relationship_record.caregiver.user.first_name == form_data['first_name']
    assert relationship_record.caregiver.user.last_name == form_data['last_name']


def test_caregiver_access_update_form_self_pass(relationship_user: Client) -> None:
    """Ensure patient cannot have different name from caregiver in self relationship."""
    patient = factories.Patient()
    relationshiptype = factories.RelationshipType(role_type=models.RoleType.SELF)
    relationship = factories.Relationship(patient=patient, type=relationshiptype)

    cancel_url = 'patient/test/?search-query'
    form_data = model_to_dict(relationship)
    form_data['pk'] = relationship.pk
    form_data['type'] = relationship.type.pk
    form_data['first_name'] = 'test_firstname'
    form_data['last_name'] = 'test_lastname'
    form_data['cancel_url'] = cancel_url

    err_msg = 'A self-relationship was selected but the caregiver appears to be someone other than the patient.'
    url = reverse('patients:relationships-view-update', kwargs={'pk': relationship.pk})

    post_response = relationship_user.post(
        path=url,
        data=form_data,
    )
    form_context = post_response.context['form']

    assert err_msg in form_context.errors.get(NON_FIELD_ERRORS)
    # assert the first and last name have not been changed
    relationship_record = models.Relationship.objects.get(pk=relationship.pk)
    assert relationship_record.caregiver.user.first_name != form_data['first_name']
    assert relationship_record.caregiver.user.last_name != form_data['last_name']


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


def test_relationship_update_up_validate(relationship_user: Client) -> None:
    """The manage caregiver access update view handles up-validate requests and does not validate the form."""
    relationship = factories.Relationship(
        type=models.RelationshipType.objects.parent_guardian(),
        status=models.RelationshipStatus.PENDING,
    )
    form_data = model_to_dict(relationship)
    form_data['type'] = models.RelationshipType.objects.self_type()

    response = relationship_user.post(
        path=reverse('patients:relationships-view-update', kwargs={'pk': relationship.pk}),
        HTTP_X_Up_Validate='type',
    )

    assert response.status_code == HTTPStatus.OK

    form: forms.forms.Form = response.context['form']

    assert not form.is_bound
    assert not form.data
    assert 'cancel_url' in response.context


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


@pytest.mark.xfail(condition=True, reason='the sidebar menus are removed', strict=True)
def test_relationships_response_contains_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that pending relationships is displayed for users with permission."""
    user = django_user_model.objects.create(username='test_relationship_user')
    user_client.force_login(user)
    permission = Permission.objects.get(codename='can_manage_relationships')
    user.user_permissions.add(permission)

    response = user_client.get(reverse('hospital-settings:index'))

    assertContains(response, 'Manage Caregiver Access')


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
    url_name: str,
) -> None:
    """Ensure that `RelationshipType` can be accessed with the required permission."""
    factories.RelationshipType(pk=11)

    response = relationshiptype_user.get(url_name)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.xfail(condition=True, reason='the sidebar menus are removed', strict=True)
def test_relationshiptype_response_contains_menu(relationshiptype_user: Client) -> None:
    """Ensures that pending relationshiptypes is displayed for users with permission."""
    response = relationshiptype_user.get(reverse('hospital-settings:index'))

    assertContains(response, 'Relationship Types')


def test_relationshiptype_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that pending relationshiptypes is not displayed for users without permission."""
    user = django_user_model.objects.create(username='test_relationshiptype_user')
    user_client.force_login(user)

    response = user_client.get(reverse('hospital-settings:index'))

    assertNotContains(response, 'Relationship Types')


def test_caregiver_access_tables_displayed_by_mrn(relationship_user: Client) -> None:
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


def test_not_display_duplicated_patients(relationship_user: Client) -> None:
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

    caregiver_profile = factories.CaregiverProfile()
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


def test_caregiver_access_tables_displayed_by_ramq(relationship_user: Client) -> None:
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


def test_caregiver_access_filter_up_validate(relationship_user: Client) -> None:
    """Ensure that the manage caregiver access filter handles up-validate requests without validation errors."""
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
        'medical_number': '',
    }
    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-list'),
        QUERY_STRING=query_string,
        HTTP_X_Up_Validate='card_type',
    )

    assert response.status_code == HTTPStatus.OK

    form: forms.forms.Form = response.context['filter'].form

    assert not form.is_bound
    assert not form.data
    assertNotContains(response, 'This field is required')


# Access Request Tests
def test_access_request_permission(client: Client, registration_user: User) -> None:
    """Ensure that the access request view can be viewed with the `can_perform_registration` permission."""
    response = client.get(reverse('patients:access-request'))

    assert response.status_code == HTTPStatus.OK


def test_access_request_no_permission(django_user_model: User) -> None:
    """Ensure that the access request view can not be viewed without the `can_perform_registration` permission."""
    request = RequestFactory().get(reverse('patients:access-request'))
    request.user = django_user_model.objects.create(username='testuser')

    with pytest.raises(PermissionDenied):
        AccessRequestView.as_view()(request)


@pytest.mark.xfail(condition=True, reason='the sidebar menus are removed', strict=True)
def test_access_request_menu_shown(client: Client, registration_user: User) -> None:
    """Ensures that Opal Registration is displayed for users with permission."""
    response = client.get(reverse('start'), follow=True)

    assertContains(response, 'Opal Registration')


def test_access_request_menu_hidden(user_client: Client) -> None:
    """Ensures that Opal Registration is not displayed for users without permission."""
    response = user_client.get(reverse('start'), follow=True)

    assertNotContains(response, 'Opal Registration')


def test_access_request_cancel_button(client: Client, registration_user: User) -> None:
    """Ensure the cancel button links to the correct URL."""
    url = reverse('patients:access-request')

    response = client.get(url)

    assertContains(response, f'href="{url}"')


def test_access_request(client: Client, registration_user: User) -> None:
    """Ensure that a GET request shows the initial search form."""
    session = client.session
    session[AccessRequestView.session_key_name] = {'random': 'data'}

    response = client.get(reverse('patients:access-request'))

    assert response.status_code == HTTPStatus.OK
    expected_data: dict[str, Any] = {}
    assert client.session[AccessRequestView.session_key_name] == expected_data
    assert 'management_form' in response.context
    assert 'search_form' in response.context
    assert 'next_button_text' in response.context


def test_access_request_get_prefix() -> None:
    """The get_prefix function can handle non-existent forms."""
    view = AccessRequestView()

    assert view._get_prefix(forms.AccessRequestSearchPatientForm) == 'search'
    assert view._get_prefix(forms.AccessRequestSendSMSForm) is None


def test_access_request_get_forms() -> None:
    """The get_forms function can handle empty forms."""
    view = AccessRequestView()
    view.forms = OrderedDict()

    assert not view._get_forms('search')


def test_access_request_invalid_management_form(registration_user: User) -> None:
    """Ensure that a missing step raises an exception."""
    request = RequestFactory().post(reverse('patients:access-request'), data={'current_step': ''})
    request.user = registration_user

    view = AccessRequestView.as_view()
    with pytest.raises(SuspiciousOperation, match='ManagementForm data is missing or has been tampered with.'):
        view(request)


def test_access_request_invalid_step(client: Client, registration_user: User) -> None:
    """Ensure that an invalid step is detected and the initial page shown."""
    response = client.post(reverse('patients:access-request'), data={'current_step': 'invalid'})

    assert response.status_code == HTTPStatus.OK
    # the session was reset
    expected_data: dict[str, Any] = {}
    assert client.session[AccessRequestView.session_key_name] == expected_data


def test_access_request_no_session_data(client: Client, registration_user: User) -> None:
    """Ensure that no initialized session data is detected and the initial page shown."""
    response = client.post(reverse('patients:access-request'), data={'current_step': 'search'})

    assert response.status_code == HTTPStatus.OK
    # the session was initialized
    expected_data: dict[str, Any] = {}
    assert client.session[AccessRequestView.session_key_name] == expected_data


def _initialize_session(client: Client, extra_data: dict[str, Any] | None = None) -> None:
    session = client.session

    data = {}
    if extra_data:
        data.update(extra_data)

    session[AccessRequestView.session_key_name] = data
    session.save()


def test_access_request_search_existing_patient(client: Client, registration_user: User) -> None:
    """Ensure that the patient search form finds the patient and moves to the next step."""
    _initialize_session(client)
    hospital_patient = factories.HospitalPatient()

    form_data = {
        'current_step': 'search',
        'search-card_type': constants.MedicalCard.MRN.name,
        'search-medical_number': hospital_patient.mrn,
        'next': 'submit',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)

    # assert that the patient was found and the next step (showing the patient) is active
    assert response.status_code == HTTPStatus.OK
    assert response.context['current_step'] == 'search'
    assert response.context['next_step'] == 'patient'
    assert 'patient_form' in response.context
    assert 'patient_table' in response.context

    # the table shows the correct patient
    table: tables.PatientTable = response.context['patient_table']

    assert table.data.data == [hospital_patient.patient]
    # the form's data was saved and models were converted to their pk only
    session = client.session[AccessRequestView.session_key_name]
    assert session == {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'patient': hospital_patient.patient.pk,
    }


def test_access_request_search_up_validate(client: Client, registration_user: User) -> None:
    """Ensure that the access request can handle up-validate events."""
    _initialize_session(client)
    hospital_patient = factories.HospitalPatient()

    form_data = {
        'current_step': 'search',
        'next': 'submit',
        'search-card_type': constants.MedicalCard.RAMQ.name,
        'search-medical_number': hospital_patient.mrn,
    }

    response = client.post(
        reverse('patients:access-request'),
        data=form_data,
        HTTP_X_Up_Validate='search-card_type',
    )

    # assert that the patient was found and the next step (showing the patient) is active
    assert response.status_code == HTTPStatus.OK
    assert response.context['current_step'] == 'search'
    assert response.context['next_step'] == 'search'

    # the data is empty and initial has the form data to not cause invalid forms
    assert response.context['search_form'].initial == {
        'current_step': 'search',
        'next': 'submit',
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': hospital_patient.mrn,
    }
    assert not response.context['search_form'].data


def test_access_request_search_fields_disabled(client: Client, registration_user: User) -> None:
    """Ensure that the patient search form fields are disabled when moving to the next step."""
    _initialize_session(client)
    hospital_patient = factories.HospitalPatient()

    form_data = {
        'current_step': 'search',
        'search-card_type': constants.MedicalCard.MRN.name,
        'search-medical_number': hospital_patient.mrn,
        'next': 'submit',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)

    form: forms.AccessRequestSearchPatientForm = response.context['search_form']
    assert form.fields['card_type'].disabled
    assert form.fields['site'].disabled
    assert form.fields['medical_number'].disabled
    assert form['card_type'].value() == constants.MedicalCard.MRN.name
    assert form['site'].value() == hospital_patient.site.pk
    assert form['medical_number'].value() == hospital_patient.mrn


def test_access_request_search_new_patient(client: Client, registration_user: User, mocker: MockerFixture) -> None:
    """Ensure that the patient search form finds a new patient and moves to the next step."""
    _initialize_session(client)
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )

    form_data = {
        'current_step': 'search',
        'search-card_type': constants.MedicalCard.RAMQ.name,
        'search-medical_number': 'MARG99991313',
        'next': 'submit',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)

    # assert that the patient was found and the next step (showing the patient) is active
    assert response.status_code == HTTPStatus.OK
    assert response.context['current_step'] == 'search'
    assert response.context['next_step'] == 'patient'
    assert 'patient_form' in response.context
    assert 'patient_table' in response.context

    # the table is shown with the correct patient data
    table: tables.PatientTable = response.context['patient_table']
    assert len(table.data.data) == 1
    patient = table.data.data[0]
    # spot check only since some dates are datetimes others are strings
    assert patient.first_name == OIE_PATIENT_DATA.first_name
    assert patient.last_name == OIE_PATIENT_DATA.last_name
    assert patient.ramq == OIE_PATIENT_DATA.ramq
    assert patient.date_of_birth == OIE_PATIENT_DATA.date_of_birth
    assert patient.mrns == OIE_PATIENT_DATA.mrns

    # the form's data was saved and models were converted to their pk only
    session = client.session[AccessRequestView.session_key_name]

    patient_data = OIE_PATIENT_DATA._asdict()
    patient_data['mrns'] = [mrn._asdict() for mrn in patient_data['mrns']]
    patient_json = json.dumps(patient_data, cls=DjangoJSONEncoder)

    assert session == {
        'step_search': {
            'card_type': constants.MedicalCard.RAMQ.name,
            'site': None,
            'medical_number': 'MARG99991313',
        },
        'patient': patient_json,
    }


def test_access_request_search_not_found(client: Client, registration_user: User, mocker: MockerFixture) -> None:
    """Ensure that the patient search form is invalid when no patient is found."""
    _initialize_session(client)
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'error',
            'data': {'message': 'patient not found'},
        },
    )

    form_data = {
        'current_step': 'search',
        'search-card_type': constants.MedicalCard.RAMQ.name,
        'search-medical_number': 'MARG99991313',
        'next': 'submit',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)

    # assert that the patient was found and the next step (showing the patient) is active
    assert response.status_code == HTTPStatus.OK
    assert response.context['current_step'] == 'search'
    assert response.context['next_step'] == 'search'
    assert 'patient_form' not in response.context
    assert 'patient_table' not in response.context


def test_access_request_confirm_patient(client: Client, registration_user: User) -> None:
    """Ensure that a patient can be confirmed and moved to the requestor step."""
    hospital_patient = factories.HospitalPatient()
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'patient',
        'next': 'submit',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)

    assert response.status_code == HTTPStatus.OK
    assert response.context['next_step'] == 'relationship'
    assert 'relationship_form' in response.context
    assert 'user_table' in response.context
    session = client.session[AccessRequestView.session_key_name]
    expected_data: dict[str, Any] = {}
    assert session['step_patient'] == expected_data


def test_access_request_requestor_new_user(client: Client, registration_user: User) -> None:
    """The relationship step handles a new user and moves to the confirm password step."""
    hospital_patient = factories.HospitalPatient()
    self_type = models.RelationshipType.objects.self_type()
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'step_patient': {},
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'relationship',
        'next': 'submit',
        'relationship-relationship_type': self_type.pk,
        'relationship-id_checked': True,
        'relationship-user_type': constants.UserType.NEW.name,
        # purposefully pass a different name to ensure that it will be ignored
        'relationship-first_name': 'Hans',
        'relationship-last_name': 'Wurst',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)

    assert response.status_code == HTTPStatus.OK
    assert response.context['next_step'] == 'confirm'
    assert response.context['next_button_text'] == 'Generate Registration Code'
    assert 'confirm_form' in response.context

    session = client.session[AccessRequestView.session_key_name]
    expected_data = data.copy()
    expected_data.update({
        'step_relationship': {
            'relationship_type': self_type.pk,
            'form_filled': False,
            'id_checked': True,
            'user_type': constants.UserType.NEW.name,
            'first_name': 'Marge',
            'last_name': 'Simpson',
            'user_email': '',
            'user_phone': '',
        },
    })
    assert session == expected_data


def test_access_request_requestor_existing_user_not_found(client: Client, registration_user: User) -> None:
    """The relationship step handles an existing user search and does not continue if the user has not been found."""
    hospital_patient = factories.HospitalPatient()
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'step_patient': {},
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'relationship',
        'next': 'submit',
        'relationship-relationship_type': models.RelationshipType.objects.guardian_caregiver().pk,
        'relationship-form_filled': True,
        'relationship-id_checked': True,
        'relationship-user_type': constants.UserType.EXISTING.name,
        'relationship-user_email': 'marge@opalmedapps.ca',
        'relationship-user_phone': '+15141234567',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)
    assert response.status_code == HTTPStatus.OK
    assert response.context['next_step'] == 'relationship'
    assert not response.context['relationship_form'].is_valid()
    assert len(response.context['relationship_form'].errors) == 1
    assert len(response.context['relationship_form'].non_field_errors()) == 1
    assert 'confirm_form' not in response.context


def test_access_request_requestor_existing_user_found(client: Client, registration_user: User) -> None:
    """The relationship step handles an existing user search and does not continue if the user has been found."""
    hospital_patient = factories.HospitalPatient()
    caregiver = factories.CaregiverProfile(
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'step_patient': {},
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'relationship',
        # the search button was clicked instead of the default form submit button
        'search_user': 'submit',
        'relationship-user_type': constants.UserType.EXISTING.name,
        'relationship-user_email': 'marge@opalmedapps.ca',
        'relationship-user_phone': '+15141234567',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)
    assert response.status_code == HTTPStatus.OK
    assert response.context['next_step'] == 'relationship'
    assert response.context['user_table'].data.data == [caregiver.user]
    assert 'confirm_form' not in response.context


def test_access_request_requestor_existing_user(client: Client, registration_user: User) -> None:
    """The relationship step handles an existing user search and continues to the confirm password step."""
    hospital_patient = factories.HospitalPatient()
    relationship_type = models.RelationshipType.objects.guardian_caregiver()
    caregiver = factories.CaregiverProfile(
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'step_patient': {},
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'relationship',
        'next': 'submit',
        'relationship-relationship_type': relationship_type.pk,
        'relationship-form_filled': True,
        'relationship-id_checked': True,
        'relationship-user_type': constants.UserType.EXISTING.name,
        'relationship-user_email': 'marge@opalmedapps.ca',
        'relationship-user_phone': '+15141234567',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)
    assert response.status_code == HTTPStatus.OK
    assert response.context['next_step'] == 'confirm'
    assert 'confirm_form' in response.context
    assert response.context['next_button_text'] == 'Create Access Request'

    session = client.session[AccessRequestView.session_key_name]
    expected_data = data.copy()
    expected_data.update({
        'step_relationship': {
            'relationship_type': relationship_type.pk,
            'form_filled': True,
            'id_checked': True,
            'user_type': constants.UserType.EXISTING.name,
            'first_name': '',
            'last_name': '',
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
        'caregiver': caregiver.pk,
    })
    assert session == expected_data


def test_access_request_confirm_password_invalid(
    client: Client,
    registration_user: User,
    mocker: MockerFixture,
) -> None:
    """The confirm password step handles an invalid password and the previous form is still valid."""
    # mock authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = False

    hospital_patient = factories.HospitalPatient()
    relationship_type = models.RelationshipType.objects.guardian_caregiver()
    caregiver = factories.CaregiverProfile(
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'step_patient': {},
        'step_relationship': {
            'relationship_type': relationship_type.pk,
            'form_filled': True,
            'id_checked': True,
            'user_type': constants.UserType.EXISTING.name,
            'first_name': '',
            'last_name': '',
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
        'caregiver': caregiver.pk,
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'confirm',
        'next': 'submit',
        'confirm-password': 'invalid',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)
    assert response.status_code == HTTPStatus.OK
    assert response.context['next_step'] == 'confirm'

    # ensure that the password is not stored in the session data
    session = client.session[AccessRequestView.session_key_name]
    assert 'step_confirm' not in session

    # ensure that the existing user is still there (see QSCCD-1262)
    assert response.context['relationship_form'].is_valid()
    assert response.context['user_table'].data.data == [caregiver.user]


def test_access_request_confirm_password_existing_user(
    client: Client,
    registration_user: User,
    mocker: MockerFixture,
) -> None:
    """The confirm password step handles an invalid password and the previous form is still valid."""
    # mock authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = False

    hospital_patient = factories.HospitalPatient()
    relationship_type = models.RelationshipType.objects.guardian_caregiver()
    caregiver = factories.CaregiverProfile(
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'step_patient': {},
        'step_relationship': {
            'relationship_type': relationship_type.pk,
            'form_filled': True,
            'id_checked': True,
            'user_type': constants.UserType.EXISTING.name,
            'first_name': '',
            'last_name': '',
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
        'caregiver': caregiver.pk,
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'confirm',
        'next': 'submit',
        'confirm-password': 'testpassword',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == reverse('patients:access-request-confirmation')

    # ensure that the relationship was created
    relationship = models.Relationship.objects.get()
    assert relationship.type == relationship_type
    assert relationship.patient == hospital_patient.patient
    assert relationship.caregiver == caregiver

    # ensure the required data by the confirmation page is in the session
    session = client.session[AccessRequestView.session_key_name]
    assert session == {
        'patient': 'Simpson, Marge',
        'requestor': 'Simpson, Marge',
        'registration_code': None,
    }


def test_access_request_confirm_password_new_user(
    client: Client,
    registration_user: User,
    mocker: MockerFixture,
) -> None:
    """The confirm password step handles an invalid password and the previous form is still valid."""
    # mock authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = False

    hospital_patient = factories.HospitalPatient()
    relationship_type = models.RelationshipType.objects.guardian_caregiver()
    data = {
        'step_search': {
            'card_type': constants.MedicalCard.MRN.name,
            'site': hospital_patient.site.pk,
            'medical_number': hospital_patient.mrn,
        },
        'step_patient': {},
        'step_relationship': {
            'relationship_type': relationship_type.pk,
            'form_filled': True,
            'id_checked': True,
            'user_type': constants.UserType.NEW.name,
            'first_name': 'Ned',
            'last_name': 'Flanders',
            'user_email': '',
            'user_phone': '',
        },
        'patient': hospital_patient.patient.pk,
    }
    _initialize_session(client, data)

    form_data = {
        'current_step': 'confirm',
        'next': 'submit',
        'confirm-password': 'testpassword',
    }

    response = client.post(reverse('patients:access-request'), data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == reverse('patients:access-request-confirmation')

    # ensure that the relationship was created
    relationship = models.Relationship.objects.get()
    caregiver = Caregiver.objects.get()
    assert relationship.type == relationship_type
    assert relationship.patient == hospital_patient.patient
    assert relationship.caregiver.user == caregiver

    registration_code = RegistrationCode.objects.get()

    # ensure the required data by the confirmation page is in the session
    session = client.session[AccessRequestView.session_key_name]
    assert session == {
        'patient': 'Simpson, Marge',
        'requestor': 'Flanders, Ned',
        'registration_code': registration_code.code,
    }


def test_access_request_confirmation_no_permission(django_user_model: User) -> None:
    """Ensure that the access request confirmation view can not be viewed without the required permission."""
    request = RequestFactory().get(reverse('patients:access-request-confirmation'))
    request.user = django_user_model.objects.create(username='testuser')

    with pytest.raises(PermissionDenied):
        AccessRequestView.as_view()(request)


def test_access_request_confirmation_no_data_redirects(client: Client, registration_user: User) -> None:
    """Ensure that the confirmation view redirects when there is no data in the session."""
    # initialize the session storage
    response = client.get(reverse('patients:access-request-confirmation'))

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == reverse('patients:access-request')


def test_access_request_confirmation_partial_data_redirects(client: Client, registration_user: User) -> None:
    """Ensure that the confirmation view redirects when there is only partial data in the session."""
    session = client.session
    session[AccessRequestView.session_key_name] = {
        'patient': 'Hans Wurst',
        'requestor': 'John Wayne',
    }
    session.save()

    response = client.get(reverse('patients:access-request-confirmation'))

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == reverse('patients:access-request')


def test_access_request_confirmation_no_code(client: Client, registration_user: User) -> None:
    """Ensure that the confirmation view shows the confirmation template for an existing user without a code."""
    session = client.session
    session[AccessRequestView.session_key_name] = {
        'patient': 'Hans Wurst',
        'requestor': 'John Wayne',
        'registration_code': None,
    }
    session.save()
    hospital_factories.Institution()

    # initialize the session storage
    response = client.get(reverse('patients:access-request-confirmation'))

    assert response.status_code == HTTPStatus.OK
    # the registration data was deleted
    assert not client.session[AccessRequestView.session_key_name]
    # the response displays the correct information
    assertTemplateUsed(response, 'patients/access_request/confirmation.html')
    assertContains(response, 'Hans Wurst')
    assertContains(response, 'John Wayne')
    url = reverse('patients:access-request')
    assertContains(response, f'href="{url}"')


def test_access_request_confirmation_code(client: Client, registration_user: User) -> None:
    """Ensure that the confirmation view shows the confirmation template for a new user with the code."""
    data = {
        'patient': 'Hans Wurst',
        'requestor': 'John Wayne',
        'registration_code': '123456',
    }
    hospital_factories.Institution()
    session = client.session
    session[AccessRequestView.session_key_name] = data
    session.save()

    # initialize the session storage
    response = client.get(reverse('patients:access-request-confirmation'))

    assert response.status_code == HTTPStatus.OK
    # the registration data was not deleted
    assert client.session[AccessRequestView.session_key_name] == data
    # the response displays the correct information
    assertTemplateUsed(response, 'patients/access_request/confirmation_code.html')
    assert 'form' in response.context
    assertContains(response, 'Hans Wurst')
    assertContains(response, 'John Wayne')
    assertContains(response, '123456')
    url = reverse('patients:access-request')
    assertContains(response, f'href="{url}"')


def test_access_request_confirmation_post_no_code(client: Client, registration_user: User) -> None:
    """Ensure that the confirmation view prevents posts when there is no code."""
    data = {
        'patient': 'Hans Wurst',
        'requestor': 'John Wayne',
        'registration_code': None,
    }
    session = client.session
    session[AccessRequestView.session_key_name] = data
    session.save()

    # initialize the session storage
    response = client.post(reverse('patients:access-request-confirmation'))

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == reverse('patients:access-request')


def test_access_request_confirmation_post_no_data(client: Client, registration_user: User) -> None:
    """Ensure that the confirmation view handles posts for the form."""
    data = {
        'patient': 'Hans Wurst',
        'requestor': 'John Wayne',
        'registration_code': '123456',
    }
    hospital_factories.Institution()
    session = client.session
    session[AccessRequestView.session_key_name] = data
    session.save()

    # initialize the session storage
    response = client.post(reverse('patients:access-request-confirmation'))

    assert response.status_code == HTTPStatus.OK
    # the registration data was not deleted
    assert client.session[AccessRequestView.session_key_name] == data


def test_access_request_confirmation_post_success(
    client: Client,
    registration_user: User,
    mocker: MockerFixture,
) -> None:
    """Ensure that the confirmation view handles posts for the form and re-shows the template on success."""
    mock_send = mocker.patch('opal.services.twilio.TwilioService.send_sms')

    data = {
        'patient': 'Hans Wurst',
        'requestor': 'John Wayne',
        'registration_code': '123456',
    }
    hospital_factories.Institution()
    session = client.session
    session[AccessRequestView.session_key_name] = data
    session.save()

    # initialize the session storage
    response = client.post(
        reverse('patients:access-request-confirmation'),
        {
            'language': 'en',
            # magic Twilio number: https://www.twilio.com/docs/iam/test-credentials#test-sms-messages-parameters-To
            'phone_number': '+15005550001',
        },
    )

    assert response.status_code == HTTPStatus.OK
    mock_send.assert_called_once_with('+15005550001', mocker.ANY)
    assertContains(response, 'SMS sent successfully')
    # the template still contains the relevant data
    assertContains(response, 'Hans Wurst')
    assertContains(response, 'John Wayne')
    assertContains(response, '123456')
    # the registration data was deleted
    assert not client.session[AccessRequestView.session_key_name]
