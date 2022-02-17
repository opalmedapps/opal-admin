from http import HTTPStatus

from django.test import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


# INDEX PAGE

def test_index_page_url_exists(client: Client) -> None:
    """This test ensures that the hospital settings index page URL exists at desired location."""
    response = client.get('/hospital-settings/')
    assert response.status_code == HTTPStatus.OK


def test_index_page_url_accessible_by_name(client: Client) -> None:
    """This test ensures that the hospital settings index page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:index')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_index_page_uses_correct_template(client: Client) -> None:
    """This test ensures that the hospital settings index page uses correct template."""
    url = reverse('hospital-settings:index')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/index.html')


# INSTITUTION LIST

def test_institution_list_url_exists(client: Client) -> None:
    """This test ensures that the institution list page URL exists at desired location."""
    response = client.get('/hospital-settings/institutions/')
    assert response.status_code == HTTPStatus.OK


def test_institution_list_accessible_by_name(client: Client) -> None:
    """This test ensures that the institution list page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-list')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_list_uses_correct_template(client: Client) -> None:
    """This test ensures that the institution list page uses correct template."""
    url = reverse('hospital-settings:institution-list')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_list.html')


# INSTITUTION DETAIL

def test_institution_detail_url_exists(client: Client, institution: Institution) -> None:
    """This test ensures that the institution detail page URL exists at desired location."""
    response = client.get('/hospital-settings/institution/{0}/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_accessible_by_name(client: Client, institution: Institution) -> None:
    """This test ensures that the institution detail page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-detail', args=(institution.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_uses_correct_template(client: Client, institution: Institution) -> None:
    """This test ensures that the institution detail page uses correct template."""
    url = reverse('hospital-settings:institution-detail', args=(institution.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_detail.html')


# INSTITUTION CREATE

def test_institution_create_url_exists(client: Client) -> None:
    """This test ensures that the institution detail page URL exists at desired location."""
    response = client.get('/hospital-settings/institution/create/')
    assert response.status_code == HTTPStatus.OK


def test_institution_create_accessible_by_name(client: Client) -> None:
    """This test ensures that the institution create page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-create')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_create_uses_correct_template(client: Client) -> None:
    """This test ensures that the institution create page uses correct template."""
    url = reverse('hospital-settings:institution-create')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_successful_create_redirects(client: Client) -> None:
    """Ensures that after a successful creation of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


# INSTITUTION UPDATE

def test_institution_update_url_exists(client: Client, institution: Institution) -> None:
    """This test ensures that the institution update page URL exists at desired location."""
    response = client.get('/hospital-settings/institution/{0}/update/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.OK


def test_institution_update_accessible_by_name(client: Client, institution: Institution) -> None:
    """This test ensures that the institution update page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_update_uses_correct_template(client: Client, institution: Institution) -> None:
    """This test ensures that the institution update page uses correct template."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_successful_update_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successful update of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


# INSTITUTION DELETE

def test_institution_delete_url_exists(client: Client, institution: Institution) -> None:
    """This test ensures that the institution delete URL exists at desired location."""
    response = client.delete('/hospital-settings/institution/{0}/delete/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.FOUND


def test_institution_delete_accessible_by_name(client: Client, institution: Institution) -> None:
    """This test ensures that the institution delete page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = client.delete(url)
    assert response.status_code == HTTPStatus.FOUND


def test_institution_delete_confirmation_template(client: Client, institution: Institution) -> None:
    """This test ensures that the institution delete page uses correct confirmation template."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_confirm_delete.html')


def test_institution_successful_delete_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successful delete of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = client.delete(url)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


def test_institution_deleted(client: Client, institution: Institution) -> None:
    """This test ensures that an institution is deleted from the database."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    client.delete(url)
    assert Institution.objects.count() == 0


# TODO: pagination, ordering, restricted to logged in users

# SITE LIST

def test_site_list_url_exists(client: Client) -> None:
    """This test ensures that the site list page URL exists at desired location."""
    response = client.get('/hospital-settings/sites/')
    assert response.status_code == HTTPStatus.OK


def test_site_list_accessible_by_name(client: Client) -> None:
    """This test ensures that the site list page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-list')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_list_uses_correct_template(client: Client) -> None:
    """This test ensures that the site list page uses correct template."""
    url = reverse('hospital-settings:site-list')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_list.html')


# SITE DETAIL

def test_site_detail_url_exists(client: Client, site: Site) -> None:
    """This test ensures that the site detail page URL exists at desired location."""
    response = client.get('/hospital-settings/site/{0}/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.OK


def test_site_detail_accessible_by_name(client: Client, site: Site) -> None:
    """This test ensures that the site detail page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-detail', args=(site.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_detail_uses_correct_template(client: Client, site: Site) -> None:
    """This test ensures that the site detail page uses correct template."""
    url = reverse('hospital-settings:site-detail', args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_detail.html')


# SITE CREATE

def test_site_create_url_exists(client: Client) -> None:
    """This test ensures that the site create page URL exists at desired location."""
    response = client.get('/hospital-settings/site/create/')
    assert response.status_code == HTTPStatus.OK


def test_site_create_accessible_by_name(client: Client) -> None:
    """This test ensures that the site create page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-create')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_create_uses_correct_template(client: Client) -> None:
    """This test ensures that the site create page uses correct template."""
    url = reverse('hospital-settings:site-create')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_successful_create_redirects(client: Client, institution: Institution) -> None:
    """Ensures that after a successful creation of a site, the page is redirected to the list page."""
    url = reverse('hospital-settings:site-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }
    response = client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:site-list'))


# SITE UPDATE

def test_site_update_url_exists(client: Client, site: Site) -> None:
    """This test ensures that the site update page URL exists at desired location."""
    response = client.get('/hospital-settings/site/{0}/update/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.OK


def test_site_update_accessible_by_name(client: Client, site: Site) -> None:
    """This test ensures that the site update page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-update', args=(site.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_update_uses_correct_template(client: Client, site: Site) -> None:
    """This test ensures that the site update page uses correct template."""
    url = reverse('hospital-settings:site-update', args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_successful_update_redirects(
    client: Client,
    institution: Institution,
    site: Site,
) -> None:
    """Ensures that after a successful update of a site, the page is redirected to the list page."""
    url = reverse('hospital-settings:site-update', args=(site.id,))
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }
    response = client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:site-list'))


# SITE DELETE

def test_site_delete_url_exists(client: Client, site: Site) -> None:
    """This test ensures that the site delete URL exists at desired location."""
    response = client.delete('/hospital-settings/site/{0}/delete/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.FOUND


def test_site_delete_accessible_by_name(client: Client, site: Site) -> None:
    """This test ensures that the site delete URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    response = client.delete(url)
    assert response.status_code == HTTPStatus.FOUND


def test_site_delete_confirmation_template(client: Client, site: Site) -> None:
    """This test ensures that the site delete page uses correct confirmation template."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_confirm_delete.html')


def test_site_successful_delete_redirects(client: Client, site: Site) -> None:
    """Ensures that after a successful delete of a site, the page is redirected to the list page."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    response = client.delete(url)
    assertRedirects(response, reverse('hospital-settings:site-list'))


def test_site_deleted(client: Client, site: Site) -> None:
    """This test ensures that a site is deleted from the database."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    client.delete(url)
    assert Site.objects.count() == 0

# TODO: pagination, ordering, restricted to logged in users
