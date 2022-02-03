from http import HTTPStatus

from django.urls.base import reverse

import pytest
from rest_framework.test import APIClient

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


def test_institution_list(api_client: APIClient):
    """This test ensures that the API to list institutions works."""
    Institution.objects.create(name='Test Hospital', code='TH')
    response = api_client.get(reverse('hospital-settings:institution-list'))

    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1


def test_site_list(api_client: APIClient):
    """This test ensures that the API to list sites works."""
    institution = Institution.objects.create(name='Test Hospital', code='TH')
    Site.objects.create(name='Test Site', code='TST', institution=institution)

    response = api_client.get(reverse('hospital-settings:site-list'))

    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
