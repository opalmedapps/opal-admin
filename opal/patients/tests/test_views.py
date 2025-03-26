from http import HTTPStatus
from typing import Tuple

from django.forms.models import model_to_dict
from django.test import Client
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertQuerysetEqual, assertTemplateUsed

from .. import factories, models, tables


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
    ('patients:access-request-step', 'patients/access_request/access_request.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_patient_wizard_urls_exist(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that each step pages exists at desired URL address."""
    url = reverse(url_name, kwargs={'step': 'site'})
    response = user_client.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_patient_wizard_urls_use_correct_template(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that each step pages exist at desired URL address."""
    url = reverse(url_name, kwargs={'step': 'site'})
    response = user_client.get(url)

    assertTemplateUsed(response, template)


@pytest.mark.parametrize(('url_name', 'template'), test_patient_multiform_url_template_data)
def test_patient_wizard_current_step(
    user_client: Client,
    url_name: str,
    template: str,
) -> None:
    """Ensure that each step pages exist at desired URL address."""
    url = reverse(url_name, kwargs={'step': 'site'})
    response = user_client.get(url)
    management_form = response.context['wizard']['management_form']

    assertQuerysetEqual(management_form['current_step'].value(), 'site')
