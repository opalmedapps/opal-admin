from http import HTTPStatus

from django.forms.models import model_to_dict
from django.test import Client
from django.urls import reverse

from pytest_django.asserts import assertContains, assertQuerysetEqual

from .. import factories, models, tables


def test_relationshiptypes_list_table(user_client: Client) -> None:
    """Relationship types list uses the corresponding table."""
    response = user_client.get(reverse('patients:relationshiptype-list'))

    assert response.context['table'].__class__ == tables.RelationshipTypeTable


def test_relationshiptypes_list(user_client: Client) -> None:
    """Relationship types are listed."""
    types = [factories.RelationshipType(), factories.RelationshipType(name='Second')]

    response = user_client.get(reverse('patients:relationshiptype-list'))
    response.content.decode('utf-8')

    assertQuerysetEqual(response.context['relationshiptype_list'], models.RelationshipType.objects.order_by('id'))

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

    assert models.RelationshipType.objects.count() == 3
    assert models.RelationshipType.objects.get(name='Testname').name == relationship_type.name


def test_relationshiptype_update_get(user_client: Client) -> None:
    """An existing relationship type can be edited."""
    relationship_type = factories.RelationshipType()

    response = user_client.get(
        reverse('patients:relationshiptype-update', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )

    assertContains(response, 'Update Relationship Type')
    assertContains(response, 'value="Caregiver"')


def test_relationshiptype_update_post(user_client: Client) -> None:
    """An existing relationship type can be updated."""
    relationship_type = factories.RelationshipType()

    relationship_type.end_age = 100

    user_client.post(
        reverse('patients:relationshiptype-update', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id']),
    )

    assert models.RelationshipType.objects.get(pk=relationship_type.pk).end_age == 100


def test_relationshiptype_delete_get(user_client: Client) -> None:
    """Deleting a relationship type needs to be confirmed."""
    relationship_type = factories.RelationshipType()

    response = user_client.get(
        reverse('patients:relationshiptype-delete', kwargs={'pk': relationship_type.pk}),
        data=model_to_dict(relationship_type, exclude=['id', 'end_age']),
    )
    assertContains(response, 'Are you sure you want to delete the following relationship type: Caregiver?')


def test_relationshiptype_delete(user_client: Client) -> None:
    """An existing relationship type can be deleted."""
    relationship_type = factories.RelationshipType()

    user_client.delete(
        reverse('patients:relationshiptype-delete', kwargs={'pk': relationship_type.pk}),
    )

    assert models.RelationshipType.objects.count() == 2


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
