from http import HTTPStatus
from typing import List, Tuple

from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

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
def test_hospital_settings_urls_exist(user_client: Client, url, template) -> None:
    """This test ensures that a page exists at desired URL address."""
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_views_use_correct_template(user_client: Client, url, template) -> None:
    """This test ensures that a page uses appropriate templates."""
    response = user_client.get(url)
    assertTemplateUsed(response, template)


# INSTITUTION

# tuple with `Institution` templates and corresponding url names
test_institution_url_template_data: List[Tuple] = [
    ('hospital-settings:institution-detail', 'hospital_settings/institution/institution_detail.html'),
    ('hospital-settings:institution-update', 'hospital_settings/institution/institution_form.html'),
    ('hospital-settings:institution-delete', 'hospital_settings/institution/institution_confirm_delete.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_institution_url_template_data)
def test_institution_urls_exist(
    user_client: Client,
    institution: Institution,
    url_name,
    template,
) -> None:
    """This test ensures that `Institution` pages exists at desired URL address."""
    url = reverse(url_name, args=(institution.id,))
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url_name', 'template'), test_institution_url_template_data)
def test_institution_urls_use_correct_template(
    user_client: Client,
    institution: Institution,
    url_name,
    template,
) -> None:
    """This test ensures that `Institution` pages exists at desired URL address."""
    url = reverse(url_name, args=(institution.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, template)


def test_institution_list_displays_all(user_client: Client):
    """This test ensures that the institution list page template displays all the institutions."""
    Institution.objects.bulk_create([
        Institution(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1'),
        Institution(name_en='TEST2_EN', name_fr='TEST2_FR', code='TEST2'),
        Institution(name_en='TEST3_EN', name_fr='TEST3_FR', code='TEST3'),
    ])
    url = reverse('hospital-settings:institution-list')
    response = user_client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_institutions = soup.find('tbody').find_all('tr')
    assert len(returned_institutions) == Institution.objects.count()


def test_institution_update_object_displayed(user_client: Client, institution: Institution):
    """This test ensures that the institution detail page displays all fields."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    response = user_client.get(url)
    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'TEST1')


# SITE

# tuple with `Site` templates and corresponding url names
test_site_url_template_data: List[Tuple] = [
    ('hospital-settings:site-detail', 'hospital_settings/site/site_detail.html'),
    ('hospital-settings:site-update', 'hospital_settings/site/site_form.html'),
    ('hospital-settings:site-delete', 'hospital_settings/site/site_confirm_delete.html'),
]


@pytest.mark.parametrize(('url_name', 'template'), test_site_url_template_data)
def test_site_urls_exist(
    user_client: Client,
    site: Site,
    url_name,
    template,
) -> None:
    """This test ensures that `Site` pages exist at desired URL address."""
    url = reverse(url_name, args=(site.id,))
    response = user_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url_name', 'template'), test_site_url_template_data)
def test_site_urls_use_correct_template(
    user_client: Client,
    site: Site,
    url_name,
    template,
) -> None:
    """This test ensures that `Site` pages uses appropriate templates."""
    url = reverse(url_name, args=(site.id,))
    response = user_client.get(url)
    assertTemplateUsed(response, template)


def test_list_all_sites(user_client: Client, institution: Institution):
    """This test ensures that the site list page template displays all the institutions."""
    Site.objects.bulk_create([
        Site(
            name_en='TEST1_EN',
            name_fr='TEST1_FR',
            parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
            parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
            code='TEST1',
            institution=institution,
        ),
        Site(
            name_en='TEST2_EN',
            name_fr='TEST2_FR',
            parking_url_en='http://127.0.0.1:8000/hospital-settings/site/2/',
            parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/2/',
            code='TEST2',
            institution=institution,
        ),
        Site(
            name_en='TEST3_EN',
            name_fr='TEST3_FR',
            parking_url_en='http://127.0.0.1:8000/hospital-settings/site/3/',
            parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/3/',
            code='TEST3',
            institution=institution,
        ),
    ])
    url = reverse('hospital-settings:site-list')
    response = user_client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_sites = soup.find('tbody').find_all('tr')
    assert len(returned_sites) == Site.objects.count()


def test_site_update_object_displayed(user_client: Client, institution: Institution):
    """This test ensures that the site detail page displays all the fields."""
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=institution,
    )
    url = reverse('hospital-settings:site-update', args=(site.id,))
    response = user_client.get(url)
    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/fr')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/en')
    assertContains(response, 'TEST1')
    assertContains(response, institution.name)

# SUCCESSFUL REDIRECTS


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


def test_institution_successful_update_redirects(user_client: Client, institution: Institution) -> None:
    """Ensures that after a successful update of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = user_client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


def test_institution_successful_delete_redirects(user_client: Client, institution: Institution) -> None:
    """Ensures that after a successful delete of an institution, the page is redirected to the list page."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    response = user_client.delete(url)
    assertRedirects(response, reverse('hospital-settings:institution-list'))


def test_institution_deleted(user_client: Client, institution: Institution) -> None:
    """Ensure that an institution is deleted from the database."""
    url = reverse('hospital-settings:institution-delete', args=(institution.id,))
    user_client.delete(url)
    assert Institution.objects.count() == 0


def test_site_successful_create_redirects(user_client: Client, institution: Institution) -> None:
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
    response = user_client.post(url, data=form_data)
    assertRedirects(response, reverse('hospital-settings:site-list'))


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


def test_site_successful_delete_redirects(user_client: Client, site: Site) -> None:
    """Ensures that after a successful delete of a site, the page is redirected to the list page."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    response = user_client.delete(url)
    assertRedirects(response, reverse('hospital-settings:site-list'))


def test_site_deleted(user_client: Client, site: Site) -> None:
    """Ensure that a site is deleted from the database."""
    url = reverse('hospital-settings:site-delete', args=(site.id,))
    user_client.delete(url)
    assert Site.objects.count() == 0
