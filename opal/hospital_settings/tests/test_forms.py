from django.test import Client
from django.urls.base import reverse

import pytest

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


def test_institution_create(user_client: Client) -> None:
    """Ensure that an institution can be created successfully."""
    url = reverse('hospital-settings:institution-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TST',
    }

    user_client.post(url, data=form_data)

    assert Institution.objects.count() == 1
    assert Institution.objects.filter(code='TST').exists()


def test_institution_create_with_missing_code(user_client: Client) -> None:
    """Ensure that the institution form checks for missing code field at the moment of creating a new institution."""
    url = reverse('hospital-settings:institution-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
    }
    response = user_client.post(url, data=form_data)

    assert Institution.objects.count() == 0
    assert 'This field is required' in response.content.decode('utf-8')


def test_institution_update_with_missing_field(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution form checks for missing code field at the moment of updating an institution."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    form_data = {
        'name_en': 'TEST1_EN_EDIT',
        'name_fr': 'TEST1_FR_EDIT',
    }
    response = user_client.post(url, data=form_data)

    institution.refresh_from_db()
    assert institution.name != 'TEST1_EN_EDIT'
    assert 'This field is required' in response.content.decode('utf-8')


# SITES


def test_site_create(user_client: Client, institution: Institution) -> None:
    """Ensure that a site can be created successfully."""
    url = reverse('hospital-settings:site-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.pk,
    }

    user_client.post(url, data=form_data)

    assert Site.objects.count() == 1
    assert Site.objects.filter(code='TEST1').exists()


def test_site_create_with_missing_field(user_client: Client) -> None:
    """Ensure that the site form checks for missing institution field at the moment of creating a new site."""
    url = reverse('hospital-settings:site-create')
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
    }
    response = user_client.post(url, data=form_data)
    assert 'This field is required' in response.content.decode('utf-8')


def test_site_update_with_missing_field(user_client: Client, site: Site) -> None:
    """Ensure that the site form checks for missing institution field at the moment of updating a site."""
    url = reverse('hospital-settings:site-update', args=(site.id,))
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
    }
    response = user_client.post(url, data=form_data)

    assert 'This field is required' in response.content.decode('utf-8')
