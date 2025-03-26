from http import HTTPStatus

from django.urls.base import reverse

import pytest
from rest_framework.test import APIClient

from .. import factories

pytestmark = pytest.mark.django_db


def test_api_institution_unauthenticated(api_client: APIClient) -> None:
    """Ensure that the API to retrieve the singleton institution requires an authenticated user."""
    response = api_client.get(reverse('api:institution-detail'))

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_api_institution_no_permission(user_api_client: APIClient) -> None:
    """Ensure that the API to retrieve the singleton institution requires a permission."""
    response = user_api_client.get(reverse('api:institution-detail'))

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_api_institution_not_found(admin_api_client: APIClient) -> None:
    """Ensure that a 404 is returned if there is no institution."""
    response = admin_api_client.get(reverse('api:institution-detail'))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_api_institution(admin_api_client: APIClient) -> None:
    """Ensure that the singleton institution is returned."""
    institution = factories.Institution(name='Test', acronym='TST')

    response = admin_api_client.get(reverse('api:institution-detail'))

    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert data['id'] == institution.pk
    assert data['name'] == 'Test'
    assert data['acronym'] == 'TST'


def test_api_institution_multiple_institutions(admin_api_client: APIClient) -> None:
    """Ensure that the singleton institution is returned."""
    factories.Institution()
    factories.Institution(name='Test', acronym='TST')

    response = admin_api_client.get(reverse('api:institution-detail'))

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
