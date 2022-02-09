from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains, assertTemplateUsed

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


# HOME PAGE

def test_index_page_uses_correct_template(client: Client):
    """This test ensures that the hospital settings index page uses correct template."""
    url = reverse('index')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/index.html')


# INSTITUTION

def test_institution_list_uses_correct_template(client: Client):
    """This test ensures that the institution list page uses correct template."""
    url = reverse('institution-list')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_list.html')


def test_institution_list_dislplays_all(client: Client):
    """This test ensures that the institution list page template displays all the institutions."""
    Institution.objects.bulk_create([
        Institution(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1'),
        Institution(name_en='TEST2_EN', name_fr='TEST2_FR', code='TEST2'),
        Institution(name_en='TEST3_EN', name_fr='TEST3_FR', code='TEST3'),
    ])
    url = reverse('institution-list')
    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_number_of_insts = len(soup.find_all('tr'))
    assert returned_number_of_insts >= Institution.objects.count()


def test_institution_detail_uses_correct_template(client: Client, institution: Institution):
    """This test ensures that the institution detail page uses correct template."""
    url = reverse('institution-detail', args=(institution.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_detail.html')


def test_institution_create_uses_correct_template(client: Client):
    """This test ensures that the institution create page uses correct template."""
    url = reverse('institution-create')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_update_uses_correct_template(client: Client, institution: Institution):
    """This test ensures that the institution update page uses correct template."""
    url = reverse('institution-update', args=(institution.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_update_object_displayed(client: Client, institution: Institution):
    """This test ensures that the institution detail page displays all fields."""
    url = reverse('institution-update', args=(institution.id,))
    response = client.get(url)
    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'TEST1')


# SITES


def test_site_list_uses_correct_template(client: Client):
    """This test ensures that the site list page uses correct template."""
    url = reverse('site-list')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_list.html')


def test_list_all_sites(client: Client, institution: Institution):
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
    url = reverse('site-list')
    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_number_of_sites = len(soup.find_all('tr'))
    assert returned_number_of_sites >= Site.objects.count()


def test_site_detail_uses_correct_template(client: Client, institution: Institution):
    """This test ensures that the site detail page uses correct template."""
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=institution,
    )
    url = reverse('site-detail', args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_detail.html')


def test_site_create_uses_correct_template(client: Client):
    """This test ensures that the site create page uses correct template."""
    url = reverse('site-create')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_update_uses_correct_template(client: Client, institution: Institution):
    """This test ensures that the site update page uses correct template."""
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=institution,
    )
    url = reverse('site-update', args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_update_object_displayed(client: Client, institution: Institution):
    """This test ensures that the site detail page displays all the fields."""
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=institution,
    )
    url = reverse('site-update', args=(site.id,))
    response = client.get(url)
    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/fr')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/en')
    assertContains(response, 'TEST1')
    assertContains(response, institution.name)
