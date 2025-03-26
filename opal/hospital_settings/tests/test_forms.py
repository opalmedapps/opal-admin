from django.test import Client
from django.urls.base import reverse

import pytest

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


def test_institution_create_with_missing_code(client: Client) -> None:
    """Ensures that the institution form checks for missing code field at the moment of creating a new institution."""
    url = reverse('institution-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')


def test_institution_update_with_missing_field(client: Client, institution: Institution) -> None:
    """Ensures that the institution form checks for missing code field at the moment of updating an institution."""
    url = reverse('institution-update', args=(institution.id,))
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')


# SITES


def test_site_create_with_missing_field(client: Client) -> None:
    """Ensures that the site form checks for missing institution field at the moment of creating a new site."""
    url = reverse('site-create')
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')


def test_site_update_with_missing_field(client: Client) -> None:
    """Ensures that the site form checks for missing institution field at the moment of updating a site."""
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES'),
    )
    url = reverse('site-update', args=(site.id,))
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')
