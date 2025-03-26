from django.test import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertRedirects

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


def test_institution_successfull_create_redirects(client: Client) -> None:
    """Ensures that after a successfull creation of an institution, the page is redirected to the list page."""
    url = reverse('institution-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assertRedirects(response, reverse('institution-list'))


def test_institution_successfull_update_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successfull update of an institution, the page is redirected to the list page."""
    url = reverse('institution-update', args=(institution.id,))
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assertRedirects(response, reverse('institution-list'))


def test_institution_successfull_delete_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successfull delete of an institution, the page is redirected to the list page."""
    url = reverse('institution-delete', args=(institution.id,))
    response = client.delete(url)
    assertRedirects(response, reverse('institution-list'))


# TODO: pagination, ordering, restricted to logged in users


def test_site_successfull_create_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successfull creation of a site, the page is redirected to the list page."""
    url = reverse('site-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assertRedirects(response, reverse('site-list'))


def test_site_successfull_update_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successfull update of a site, the page is redirected to the list page."""
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=institution,
    )
    url = reverse('site-update', args=(site.id,))
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }
    response = client.post(url, data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assertRedirects(response, reverse('site-list'))


def test_site_successfull_delete_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successfull delete of a site, the page is redirected to the list page."""
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=institution,
    )
    url = reverse('site-delete', args=(site.id,))
    response = client.delete(url)
    assertRedirects(response, reverse('site-list'))

# TODO: pagination, ordering, restricted to logged in users
