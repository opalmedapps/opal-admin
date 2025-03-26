from http import HTTPStatus

from django.test import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


# INDEX PAGE

def test_index_page_url_exists(user_client: Client) -> None:
    """Ensure that the hospital settings index page URL exists at desired location."""
    response = user_client.get('/hospital-settings/')
    assert response.status_code == HTTPStatus.OK


def test_index_page_url_accessible_by_name(user_client: Client) -> None:
    """Ensure that the hospital settings index page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:index')
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_index_page_uses_correct_template(user_client: Client) -> None:
    """Ensure that the hospital settings index page uses correct template."""
    url = reverse('hospital-settings:index')
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/index.html')


# INSTITUTION LIST

def test_institution_list_url_exists(user_client: Client) -> None:
    """Ensure that the institution list page URL exists at desired location."""
    response = user_client.get('/hospital-settings/institutions/')
    assert response.status_code == HTTPStatus.OK


def test_institution_list_accessible_by_name(user_client: Client) -> None:
    """Ensure that the institution list page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-list')
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_list_uses_correct_template(user_client: Client) -> None:
    """Ensure that the institution list page uses correct template."""
    url = reverse('hospital-settings:institution-list')
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_list.html')


# INSTITUTION DETAIL

def test_institution_detail_url_exists(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution detail page URL exists at desired location."""
    response = user_client.get('/hospital-settings/institution/{0}/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_accessible_by_name(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution detail page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-detail', args=(institution.id,))
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_uses_correct_template(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution detail page uses correct template."""
    url = reverse('hospital-settings:institution-detail', args=(institution.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_detail.html')


# INSTITUTION CREATE

def test_institution_create_url_exists(user_client: Client) -> None:
    """Ensure that the institution detail page URL exists at desired location."""
    response = user_client.get('/hospital-settings/institution/create/')
    assert response.status_code == HTTPStatus.OK


def test_institution_create_accessible_by_name(user_client: Client) -> None:
    """Ensure that the institution create page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-create')
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_create_uses_correct_template(user_client: Client) -> None:
    """Ensure that the institution create page uses correct template."""
    url = reverse('hospital-settings:institution-create')
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_successful_create_redirects(user_client: Client) -> None:
    """Ensure that after a successful creation of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = user_client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


# INSTITUTION UPDATE

def test_institution_update_url_exists(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution update page URL exists at desired location."""
    response = user_client.get('/hospital-settings/institution/{0}/update/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.OK


def test_institution_update_accessible_by_name(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution update page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_update_uses_correct_template(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution update page uses correct template."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_successful_update_redirects(user_client: Client, institution: Institution) -> None:
    """Ensure that after a successful update of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = user_client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


# INSTITUTION DELETE

def test_institution_delete_url_exists(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution delete URL exists at desired location."""
    response = user_client.delete('/hospital-settings/institution/{0}/delete/'.format(str(institution.id)))
    assert response.status_code == HTTPStatus.FOUND


def test_institution_delete_accessible_by_name(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution delete page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = user_client.delete(url)
    assert response.status_code == HTTPStatus.FOUND


def test_institution_delete_confirmation_template(user_client: Client, institution: Institution) -> None:
    """Ensure that the institution delete page uses correct confirmation template."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_confirm_delete.html')


def test_institution_successful_delete_redirects(user_client: Client, institution: Institution) -> None:
    """Ensure that after a successful delete of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = user_client.delete(url)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


def test_institution_deleted(user_client: Client, institution: Institution) -> None:
    """Ensure that an institution is deleted from the database."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    user_client.delete(url)
    assert Institution.objects.count() == 0


# TODO: pagination, ordering, restricted to logged in users

# SITE LIST

def test_site_list_url_exists(user_client: Client) -> None:
    """Ensure that the site list page URL exists at desired location."""
    response = user_client.get('/hospital-settings/sites/')
    assert response.status_code == HTTPStatus.OK


def test_site_list_accessible_by_name(user_client: Client) -> None:
    """Ensure that the site list page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-list')
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_list_uses_correct_template(user_client: Client) -> None:
    """Ensure that the site list page uses correct template."""
    url = reverse('hospital-settings:site-list')
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_list.html')


# SITE DETAIL

def test_site_detail_url_exists(user_client: Client, site: Site) -> None:
    """Ensure that the site detail page URL exists at desired location."""
    response = user_client.get('/hospital-settings/site/{0}/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.OK


def test_site_detail_accessible_by_name(user_client: Client, site: Site) -> None:
    """Ensure that the site detail page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-detail', args=(site.id,))
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_detail_uses_correct_template(user_client: Client, site: Site) -> None:
    """Ensure that the site detail page uses correct template."""
    url = reverse('hospital-settings:site-detail', args=(site.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_detail.html')


# SITE CREATE

def test_site_create_url_exists(user_client: Client) -> None:
    """Ensure that the site create page URL exists at desired location."""
    response = user_client.get('/hospital-settings/site/create/')
    assert response.status_code == HTTPStatus.OK


def test_site_create_accessible_by_name(user_client: Client) -> None:
    """Ensure that the site create page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-create')
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_create_uses_correct_template(user_client: Client) -> None:
    """Ensure that the site create page uses correct template."""
    url = reverse('hospital-settings:site-create')
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_successful_create_redirects(user_client: Client, institution: Institution) -> None:
    """Ensure that after a successful creation of a site, the page is redirected to the list page."""
    url = reverse('hospital-settings:site-create')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }
    response = user_client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:site-list'))


# SITE UPDATE

def test_site_update_url_exists(user_client: Client, site: Site) -> None:
    """Ensure that the site update page URL exists at desired location."""
    response = user_client.get('/hospital-settings/site/{0}/update/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.OK


def test_site_update_accessible_by_name(user_client: Client, site: Site) -> None:
    """Ensure that the site update page URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-update', args=(site.id,))
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_update_uses_correct_template(user_client: Client, site: Site) -> None:
    """Ensure that the site update page uses correct template."""
    url = reverse('hospital-settings:site-update', args=(site.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_successful_update_redirects(
    user_client: Client,
    institution: Institution,
    site: Site,
) -> None:
    """Ensure that after a successful update of a site, the page is redirected to the list page."""
    url = reverse('hospital-settings:site-update', args=(site.id,))
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }
    response = user_client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:site-list'))


# SITE DELETE

def test_site_delete_url_exists(user_client: Client, site: Site) -> None:
    """Ensure that the site delete URL exists at desired location."""
    response = user_client.delete('/hospital-settings/site/{0}/delete/'.format(str(site.id)))
    assert response.status_code == HTTPStatus.FOUND


def test_site_delete_accessible_by_name(user_client: Client, site: Site) -> None:
    """Ensure that the site delete URL is accessible by its `name` attribute."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    response = user_client.delete(url)
    assert response.status_code == HTTPStatus.FOUND


def test_site_delete_confirmation_template(user_client: Client, site: Site) -> None:
    """Ensure that the site delete page uses correct confirmation template."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_confirm_delete.html')


def test_site_successful_delete_redirects(user_client: Client, site: Site) -> None:
    """Ensure that after a successful delete of a site, the page is redirected to the list page."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    response = user_client.delete(url)
    assertRedirects(response, reverse('hospital-settings:site-list'))


def test_site_deleted(user_client: Client, site: Site) -> None:
    """Ensure that a site is deleted from the database."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    user_client.delete(url)
    assert Site.objects.count() == 0
