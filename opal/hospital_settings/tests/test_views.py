from http import HTTPStatus
from typing import List, Tuple

from django.test import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


# INDEX PAGE

# tuple with general hospital-settings templates and corresponding url names
test_url_template_data: List[Tuple] = [
    (reverse('hospital-settings:index'), 'hospital_settings/index.html'),
    (reverse('hospital-settings:institution-list'), 'hospital_settings/institution/institution_list.html'),
    (reverse('hospital-settings:institution-create'), 'hospital_settings/institution/institution_form.html'),
    (reverse('hospital-settings:site-list'), 'hospital_settings/site/site_list.html'),
    (reverse('hospital-settings:site-create'), 'hospital_settings/site/site_form.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_hospital_settings_urls_exisit(client: Client, url, template) -> None:
    """This test ensures that a page exists at desired URL address."""
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_hs_uses_correct_template(client: Client, url, template) -> None:
    """This test ensures that a page uses appropriate templates."""
    response = client.get(url)
    assertTemplateUsed(response, template)


# INSTITUTION

# tuple with `Institution` templates and corresponding url names
test_institution_url_template_data: List[Tuple] = [
    ('hospital-settings:institution-detail', 'hospital_settings/institution/institution_detail.html'),
    ('hospital-settings:institution-update', 'hospital_settings/institution/institution_form.html'),
    ('hospital-settings:institution-delete', 'hospital_settings/institution/institution_confirm_delete.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_institution_url_template_data)
def test_hs_institution_urls_exisit(
    client: Client,
    institution: Institution,
    url_name,
    template,
) -> None:
    """This test ensures that `Institution` pages exists at desired URL address."""
    url = reverse(url_name, args=(institution.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url_name', 'template'), test_institution_url_template_data)
def test_hs_institution_uses_correct_template(
    client: Client,
    institution: Institution,
    url_name,
    template,
) -> None:
    """This test ensures that `Institution` pages uses appropriate templates."""
    url = reverse(url_name, args=(institution.id,))
    response = client.get(url)
    assertTemplateUsed(response, template)


# SITE

# tuple with `Site` templates and corresponding url names
test_site_url_template_data: List[Tuple] = [
    ('hospital-settings:site-detail', 'hospital_settings/site/site_detail.html'),
    ('hospital-settings:site-update', 'hospital_settings/site/site_form.html'),
    ('hospital-settings:site-delete', 'hospital_settings/site/site_confirm_delete.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_site_url_template_data)
def test_hs_site_urls_exisit(
    client: Client,
    site: Site,
    url_name,
    template,
) -> None:
    """This test ensures that `Site` pages exist at desired URL address."""
    url = reverse(url_name, args=(site.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url_name', 'template'), test_site_url_template_data)
def test_hs_site_uses_correct_template(
    client: Client,
    site: Site,
    url_name,
    template,
) -> None:
    """This test ensures that `Site` pages uses appropriate templates."""
    url = reverse(url_name, args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, template)


# SUCCESSFUL REDIRECTS

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
