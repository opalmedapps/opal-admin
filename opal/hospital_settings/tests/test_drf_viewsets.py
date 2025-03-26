from http import HTTPStatus

from django.urls.base import reverse

import pytest
from rest_framework.test import APIClient

from opal.users.models import User

from .. import factories

pytestmark = pytest.mark.django_db


HTTP_METHODS_READ_ONLY = 'GET, HEAD, OPTIONS'


def test_api_institutions_list(api_client: APIClient, admin_user: User) -> None:
    """Ensure that the API to list institutions works."""
    api_client.force_login(user=admin_user)

    institution = factories.Institution()
    response = api_client.get(reverse('api:institutions-list'))

    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 1
    assert response.data[0]['id'] == institution.pk


def test_api_institutions_list_allowed_methods(api_client: APIClient, admin_user: User) -> None:
    """Ensure that an institution can only be retrieved."""
    api_client.force_login(user=admin_user)

    response = api_client.options(reverse('api:institutions-list'))

    assert response.headers['Allow'] == HTTP_METHODS_READ_ONLY


def test_api_institutions_detail_allowed_methods(api_client: APIClient, admin_user: User) -> None:
    """Ensure that an institution can only be retrieved."""
    api_client.force_login(user=admin_user)
    institution = factories.Institution()

    response = api_client.options(reverse('api:institutions-detail', kwargs={'pk': institution.pk}))

    assert response.headers['Allow'] == HTTP_METHODS_READ_ONLY


def test_api_institution_retrieve(api_client: APIClient, admin_user: User) -> None:
    """Ensure that an institution can be retrieved."""
    api_client.force_login(user=admin_user)
    institution = factories.Institution()

    response = api_client.get(reverse('api:institutions-detail', kwargs={'pk': institution.pk}))

    assert response.status_code == HTTPStatus.OK
    assert response.data['id'] == institution.pk


def test_api_terms_of_use_allowed_methods(api_client: APIClient, admin_user: User) -> None:
    """Ensure that the terms of use of an institution can only be retrieved."""
    api_client.force_login(user=admin_user)
    institution = factories.Institution()

    response = api_client.get(reverse('api:institutions-terms-of-use', kwargs={'pk': institution.pk}))

    assert response.headers['Allow'] == HTTP_METHODS_READ_ONLY


def test_api_terms_of_use(api_client: APIClient, admin_user: User) -> None:
    """Ensure that the terms of use an institution can be retrieved."""
    api_client.force_login(user=admin_user)
    institution = factories.Institution()

    response = api_client.get(reverse('api:institutions-terms-of-use', kwargs={'pk': institution.pk}))

    assert response.status_code == HTTPStatus.OK
    assert response.data['id'] == institution.pk


def test_api_site_list(api_client: APIClient, admin_user: User) -> None:
    """Ensure that the API to list sites works."""
    api_client.force_login(user=admin_user)

    site = factories.Site()

    response = api_client.get(reverse('api:sites-list'))

    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 1
    assert response.data[0]['id'] == site.pk


def test_api_site_retrieve(api_client: APIClient, admin_user: User) -> None:
    """Ensure that an institution can be retrieved."""
    api_client.force_login(user=admin_user)
    site = factories.Site()

    response = api_client.get(reverse('api:sites-detail', kwargs={'pk': site.pk}))

    assert response.status_code == HTTPStatus.OK
    assert response.data['id'] == site.pk


def test_api_sites_list_allowed_methods(api_client: APIClient, admin_user: User) -> None:
    """Ensure that sites can only be retrieved."""
    api_client.force_login(user=admin_user)

    response = api_client.options(reverse('api:sites-list'))

    assert response.headers['Allow'] == HTTP_METHODS_READ_ONLY


def test_api_sites_detail_allowed_methods(api_client: APIClient, admin_user: User) -> None:
    """Ensure that a site can only be retrieved."""
    api_client.force_login(user=admin_user)
    site = factories.Site()

    response = api_client.options(reverse('api:sites-detail', kwargs={'pk': site.pk}))

    assert response.headers['Allow'] == HTTP_METHODS_READ_ONLY
