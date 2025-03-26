from http import HTTPStatus

from django.test import Client
from django.urls.base import reverse

import pytest

from ..models import Institution, Site

pytestmark = pytest.mark.django_db

# HOME PAGE


def test_index_page_url_exists(client: Client) -> None:
    """This test ensures that the hospital settings index page URL exists at desired location."""
    response = client.get('/hospital-settings/')
    assert response.status_code == HTTPStatus.OK


def test_index_page_url_accessible_by_name(client: Client) -> None:
    """This test ensures that the hospital settings index page URL is accessible by its `name` attribute."""
    url = reverse('index')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


# INSTITUTION

def test_institution_list_url_exists(client: Client) -> None:
    """This test ensures that the institution list page URL exists at desired location."""
    response = client.get('/hospital-settings/institutions/')
    assert response.status_code == HTTPStatus.OK


def test_institution_list_accessible_by_name(client: Client) -> None:
    """This test ensures that the institution list page URL is accessible by its `name` attribute."""
    url = reverse('institution-list')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_url_exists(client: Client, institution: Institution) -> None:
    """This test ensures that the institution detail page URL exists at desired location."""
    response = client.get('/hospital-settings/institution/{0}/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_accessible_by_name(client: Client, institution: Institution) -> None:
    """This test ensures that the institution detail page URL is accessible by its `name` attribute."""
    url = reverse('institution-detail', args=(institution.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_create_url_exists(client: Client) -> None:
    """This test ensures that the institution detail page URL exists at desired location."""
    response = client.get('/hospital-settings/institution/create/')
    assert response.status_code == HTTPStatus.OK


def test_institution_create_accessible_by_name(client: Client) -> None:
    """This test ensures that the institution create page URL is accessible by its `name` attribute."""
    url = reverse('institution-create')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_update_url_exists(client: Client, institution: Institution) -> None:
    """This test ensures that the institution update page URL exists at desired location."""
    response = client.get('/hospital-settings/institution/{0}/update/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.OK


def test_institution_update_accessible_by_name(client: Client, institution: Institution) -> None:
    """This test ensures that the institution update page URL is accessible by its `name` attribute."""
    url = reverse('institution-update', args=(institution.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_delete_url_exists(client: Client, institution: Institution) -> None:
    """This test ensures that the institution delete URL exists at desired location."""
    response = client.delete('/hospital-settings/institution/{0}/delete/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.FOUND


def test_institution_delete_accessible_by_name(client: Client, institution: Institution) -> None:
    """This test ensures that the institution delete page URL is accessible by its `name` attribute."""
    url = reverse('institution-delete', args=(institution.id,))
    response = client.delete(url)
    assert response.status_code == HTTPStatus.FOUND


# SITES


def test_site_list_url_exists(client: Client) -> None:
    """This test ensures that the site list page URL exists at desired location."""
    response = client.get('/hospital-settings/sites/')
    assert response.status_code == HTTPStatus.OK


def test_site_list_accessible_by_name(client: Client) -> None:
    """This test ensures that the site list page URL is accessible by its `name` attribute."""
    url = reverse('site-list')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_detail_url_exists(client: Client) -> None:
    """This test ensures that the site detail page URL exists at desired location."""
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES'),
    )
    response = client.get('/hospital-settings/site/{0}/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.OK


def test_site_detail_accessible_by_name(client: Client) -> None:
    """This test ensures that the site detail page URL is accessible by its `name` attribute."""
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES'),
    )
    url = reverse('site-detail', args=(site.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_create_url_exists(client: Client) -> None:
    """This test ensures that the site create page URL exists at desired location."""
    response = client.get('/hospital-settings/site/create/')
    assert response.status_code == HTTPStatus.OK


def test_site_create_accessible_by_name(client: Client) -> None:
    """This test ensures that the site create page URL is accessible by its `name` attribute."""
    url = reverse('site-create')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_update_url_exists(client: Client) -> None:
    """This test ensures that the site update page URL exists at desired location."""
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES'),
    )
    response = client.get('/hospital-settings/site/{0}/update/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.OK


def test_site_update_accessible_by_name(client: Client) -> None:
    """This test ensures that the site update page URL is accessible by its `name` attribute."""
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES'),
    )
    url = reverse('site-update', args=(site.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_delete_url_exists(client: Client) -> None:
    """This test ensures that the site delete URL exists at desired location."""
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES'),
    )
    response = client.delete('/hospital-settings/site/{0}/delete/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.FOUND


def test_site_delete_accessible_by_name(client: Client) -> None:
    """This test ensures that the site delete URL is accessible by its `name` attribute."""
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES'),
    )
    url = reverse('site-delete', args=(site.id,))
    response = client.delete(url)
    assert response.status_code == HTTPStatus.FOUND
