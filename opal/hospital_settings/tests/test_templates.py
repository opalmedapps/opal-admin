from django.test import Client
from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


# INSTITUTION

def test_institution_list_dislplays_all(client: Client):
    """This test ensures that the institution list page template displays all the institutions."""
    Institution.objects.bulk_create([
        Institution(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1'),
        Institution(name_en='TEST2_EN', name_fr='TEST2_FR', code='TEST2'),
        Institution(name_en='TEST3_EN', name_fr='TEST3_FR', code='TEST3'),
    ])
    url = reverse('hospital-settings:institution-list')
    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_institutions = soup.find('tbody').find_all('tr')
    assert len(returned_institutions) == Institution.objects.count()


def test_institution_update_object_displayed(client: Client, institution: Institution):
    """This test ensures that the institution detail page displays all fields."""
    url = reverse('hospital-settings:institution-update', args=(institution.id,))
    response = client.get(url)
    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'TEST1')


# SITES

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
    url = reverse('hospital-settings:site-list')
    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returned_sites = soup.find('tbody').find_all('tr')
    assert len(returned_sites) == Site.objects.count()


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
    url = reverse('hospital-settings:site-update', args=(site.id,))
    response = client.get(url)
    assertContains(response, 'TEST1_EN')
    assertContains(response, 'TEST1_FR')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/fr')
    assertContains(response, 'http://127.0.0.1:8000/hospital-settings/site/1/en')
    assertContains(response, 'TEST1')
    assertContains(response, institution.name)
