from http import HTTPStatus
from typing import Tuple

from django.contrib.auth.models import AbstractUser, Permission
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.test import Client, RequestFactory
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertNotContains, assertQuerysetEqual, assertTemplateUsed

from ...users.models import User
from .. import factories, forms, models, tables
# Add any future GET-requestable patients app pages here for faster test writing
from ..views import PendingRelationshipListView

test_url_template_data: list[Tuple] = [
    (reverse('patients:relationships-search'), 'patients/relationships-search/form.html'),
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
    response.content.decode('utf-8')

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


def test_relationships_list_table(user_client: Client) -> None:
    """Ensures Relationships list uses the corresponding table."""
    response = user_client.get(reverse('patients:relationships-pending-list'))

    assert response.context['table'].__class__ == tables.PendingRelationshipTable


def test_relationships_list_empty(user_client: Client) -> None:
    """Ensures Relationships list shows message when no types are defined."""
    response = user_client.get(reverse('patients:relationships-pending-list'))

    assert response.status_code == HTTPStatus.OK

    assertContains(response, 'No caregiver pending access requests.')


def test_relationships_pending_list(user_client: Client) -> None:
    """Ensures Relationships with pending status are listed."""
    caregivertype2 = factories.RelationshipType(name='caregiver_2')
    caregivertype3 = factories.RelationshipType(name='caregiver_3')
    relationships = [
        factories.Relationship(type=caregivertype2),
        factories.Relationship(type=caregivertype3),
    ]

    response = user_client.get(reverse('patients:relationships-pending-list'))
    response.content.decode('utf-8')

    assertQuerysetEqual(list(response.context['relationship_list']), relationships)

    for relationship in relationships:
        assertContains(response, f'<td >{relationship.type.name}</td>')  # noqa: WPS237


def test_relationships_not_pending_not_list(user_client: Client) -> None:
    """Ensures that only Relationships with pending status are listed."""
    caregivertype1 = factories.RelationshipType(name='caregiver_1')
    caregivertype2 = factories.RelationshipType(name='caregiver_2')
    caregivertype3 = factories.RelationshipType(name='caregiver_3')
    factories.Relationship(status=models.RelationshipStatus.CONFIRMED, type=caregivertype1)
    factories.Relationship(type=caregivertype2)
    factories.Relationship(type=caregivertype3)

    response = user_client.get(reverse('patients:relationships-pending-list'))

    assert len(response.context['relationship_list']) == 2


def test_relationships_pending_list_table(user_client: Client) -> None:
    """Ensures that pending relationships list uses the corresponding table."""
    response = user_client.get(reverse('patients:relationships-pending-list'))

    assert response.context['table'].__class__ == tables.PendingRelationshipTable


def test_relationships_pending_form(user_client: Client) -> None:
    """Ensures that pending relationships edit uses the right form."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    factories.Relationship(pk=1, type=relationshiptype)
    response = user_client.get(reverse('patients:relationships-pending-update', kwargs={'pk': 1}))

    assert response.context['form'].__class__ == forms.RelationshipPendingAccessForm


def test_relationships_pending_form_content(user_client: Client) -> None:
    """Ensures that pending relationships passed info is correct."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver)
    response = user_client.get(reverse('patients:relationships-pending-update', kwargs={'pk': 1}))

    assert response.context['relationship'] == relationship


def test_relationships_pending_form_response(user_client: Client) -> None:
    """Ensures that pending relationships displayed info is correct."""
    relationshiptype = factories.RelationshipType(name='relationshiptype')
    caregiver = factories.CaregiverProfile()
    patient = factories.Patient()
    relationship = factories.Relationship(pk=1, type=relationshiptype, caregiver=caregiver, patient=patient)
    response = user_client.get(reverse('patients:relationships-pending-update', kwargs={'pk': 1}))
    response.content.decode('utf-8')

    assertContains(response, patient)
    assertContains(response, caregiver)
    assertContains(response, relationship.patient.ramq)


@pytest.mark.parametrize(
    'url_name', [
        reverse('patients:relationships-pending-list'),
        reverse('patients:relationships-pending-update', args=(1,)),
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
        PendingRelationshipListView.as_view()(request)


@pytest.mark.parametrize(
    'url_name', [
        reverse('patients:relationships-pending-list'),
        reverse('patients:relationships-pending-update', args=(1,)),
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

    response = user_client.get('/hospital-settings/')

    assertContains(response, 'Pending Requests')


def test_relationships_pending_response_no_menu(user_client: Client, django_user_model: User) -> None:
    """Ensures that pending relationships is not displayed for users without permission."""
    user = django_user_model.objects.create(username='test_relationship_user')
    user_client.force_login(user)

    response = user_client.get('/hospital-settings/')

    assertNotContains(response, 'Pending Requests')
