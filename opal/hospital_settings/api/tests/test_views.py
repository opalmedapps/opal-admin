from http import HTTPStatus

from django.urls.base import reverse

import pytest
from rest_framework.test import APIClient

from opal.hospital_settings.models import Institution, Site
from opal.users.models import User

pytestmark = pytest.mark.django_db


def test_rest_api_institution_list(api_client: APIClient, admin_user: User) -> None:
    """This test ensures that the API to list institutions works."""
    api_client.force_authenticate(user=admin_user)

    Institution.objects.create(name='Test Hospital', code='TH')
    response = api_client.get(reverse('hospital-settings:api:institution-list'))

    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1


def test_rest_api_site_list(api_client: APIClient, admin_user: User) -> None:
    """This test ensures that the API to list sites works."""
    api_client.force_authenticate(user=admin_user)

    institution = Institution.objects.create(name='Test Hospital', code='TH')
    Site.objects.create(name='Test Site', code='TST', institution=institution)

    response = api_client.get(reverse('hospital-settings:api:site-list'))

    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
