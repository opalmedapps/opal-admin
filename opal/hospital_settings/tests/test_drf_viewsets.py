from http import HTTPStatus
from typing import Callable

from django.urls.base import reverse

import pytest
from rest_framework.test import APIClient

from opal.users.models import User

from .. import factories

pytestmark = pytest.mark.django_db


HTTP_METHODS_READ_ONLY = 'GET, HEAD, OPTIONS'


@pytest.mark.parametrize(('url_name', 'is_detail'), [
    ('api:institutions-list', False),
    ('api:institutions-detail', True),
    ('api:institutions-terms-of-use', True),
])
def test_institutions_unauthenticated_unauthorized(
    url_name: str,
    is_detail: bool,
    api_client: APIClient,
    user: User,
    user_with_permission: Callable[[str | list[str]], User],
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    kwargs = {'pk': factories.Institution().pk} if is_detail else {}
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(user_with_permission('hospital_settings.view_institution'))
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.OK


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


def test_api_institutions_retrieve(api_client: APIClient, admin_user: User) -> None:
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


@pytest.mark.parametrize(('url_name', 'is_detail'), [
    ('api:sites-list', False),
    ('api:sites-detail', True),
])
def test_sites_unauthenticated_unauthorized(
    url_name: str,
    is_detail: bool,
    api_client: APIClient,
    user: User,
    user_with_permission: Callable[[str | list[str]], User],
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    kwargs = {'pk': factories.Site().pk} if is_detail else {}
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(user_with_permission('hospital_settings.view_site'))
    response = api_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.OK


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
