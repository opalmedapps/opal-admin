from http import HTTPStatus

from django.urls.base import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertTemplateUsed
from rest_framework.test import APIClient

from ..models import Institution, Site

pytestmark = pytest.mark.django_db

# REST API

def test_intest_rest_api_institution_liststitution_list(api_client: APIClient):
    """This test ensures that the API to list institutions works."""
    Institution.objects.create(name='Test Hospital', code='TH')
    response = api_client.get(reverse('api-hospital-settings:institution-list'))

    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1


def test_rest_api_site_list(api_client: APIClient):
    """This test ensures that the API to list sites works."""
    institution = Institution.objects.create(name='Test Hospital', code='TH')
    Site.objects.create(name='Test Site', code='TST', institution=institution)

    response = api_client.get(reverse('api-hospital-settings:site-list'))

    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1


# HOME PAGE

def test_home_page_url_exists_at_desired_location(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK


def test_home_page_url_accessible_by_name(client):
    url = reverse('index')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_home_page_uses_correct_template(client):
    url = reverse('index')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/index.html')


# INSTITUTION

def test_institution_list_url_exists_at_desired_location(client):
    response = client.get('/hospital-settings/institutions/')
    assert response.status_code == HTTPStatus.OK


def test_institution_list_accessible_by_name(client):
    url = reverse('institution-list')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_list_uses_correct_template(client):
    url = reverse('institution-list')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_list.html')


@pytest.mark.django_db()
def test_list_all_institutions(client):
    Institution.objects.bulk_create([
        Institution(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1'),
        Institution(name_en='TEST2_EN', name_fr='TEST2_FR', code='TEST2'),
        Institution(name_en='TEST3_EN', name_fr='TEST3_FR', code='TEST3'),
    ])
    url = reverse('institution-list')
    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returnedNumberOfInsts = len(soup.find_all('tr'))
    assert returnedNumberOfInsts >= Institution.objects.count()


def test_institution_detail_url_exists_at_desired_location(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    response = client.get('/hospital-settings/institution/' + str(inst.id) + '/')
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_accessible_by_name(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-detail', args=(inst.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_detail_uses_correct_template(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-detail', args=(inst.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_detail.html')


def test_institution_create_url_exists_at_desired_location(client):
    response = client.get('/hospital-settings/institution/create/')
    assert response.status_code == HTTPStatus.OK


def test_institution_create_accessible_by_name(client):
    url = reverse('institution-create')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_create_uses_correct_template(client):
    url = reverse('institution-create')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_successfull_create_request_redirects(client):
    url = reverse('institution-create')
    data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert response.status_code == HTTPStatus.FOUND


def test_institution_create_with_missing_field(client):
    url = reverse('institution-create')
    data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')


def test_institution_update_url_exists_at_desired_location(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    response = client.get('/hospital-settings/institution/' + str(inst.id) + '/update/')
    assert response.status_code == HTTPStatus.OK


def test_institution_update_accessible_by_name(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-update', args=(inst.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_institution_update_uses_correct_template(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-update', args=(inst.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/institution/institution_form.html')


def test_institution_update_object_displayed(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-update', args=(inst.id,))
    response = client.get(url)
    assert 'TEST1_EN' in response.content.decode('utf-8') \
        and 'TEST1_FR' in response.content.decode('utf-8') \
        and 'TEST1' in response.content.decode('utf-8')


def test_institution_successfull_update_request_redirects(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-update', args=(inst.id,))
    data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TEST1',
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert response.status_code == HTTPStatus.FOUND


def test_institution_update_with_missing_field(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-update', args=(inst.id,))
    data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')


def test_institution_delete_url_exists_at_desired_location(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    response = client.delete('/hospital-settings/institution/' + str(inst.id) + '/delete/')
    assert response.status_code == HTTPStatus.FOUND


def test_institution_delete_accessible_by_name(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-delete', args=(inst.id,))
    response = client.delete(url)
    assert response.status_code == HTTPStatus.FOUND


def test_institution_deleted(client):
    inst = Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
    url = reverse('institution-delete', args=(inst.id,))
    client.delete(url)
    assert Institution.objects.filter(pk=inst.id).first() is None

# TODO: pagination, ordering, restricted to logged in users

# SITES


def test_site_list_url_exists_at_desired_location(client):
    response = client.get('/hospital-settings/sites/')
    assert response.status_code == HTTPStatus.OK


def test_site_list_accessible_by_name(client):
    url = reverse('site-list')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_list_uses_correct_template(client):
    url = reverse('site-list')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_list.html')


@pytest.mark.django_db()
def test_list_all_sites(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    Site.objects.bulk_create([
        Site(
            name_en='TEST1_EN',
            name_fr='TEST1_FR',
            parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
            parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
            code='TEST1',
            institution=Institution.objects.get(code__exact='ALL_SITES')
        ),
        Site(
            name_en='TEST2_EN',
            name_fr='TEST2_FR',
            parking_url_en='http://127.0.0.1:8000/hospital-settings/site/2/',
            parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/2/',
            code='TEST2',
            institution=Institution.objects.get(code__exact='ALL_SITES')
        ),
        Site(
            name_en='TEST3_EN',
            name_fr='TEST3_FR',
            parking_url_en='http://127.0.0.1:8000/hospital-settings/site/3/',
            parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/3/',
            code='TEST3',
            institution=Institution.objects.get(code__exact='ALL_SITES')
        ),
    ])
    url = reverse('site-list')
    response = client.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    returnedNumberOfSites = len(soup.find_all('tr'))
    assert returnedNumberOfSites >= Site.objects.count()


def test_site_detail_url_exists_at_desired_location(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    response = client.get('/hospital-settings/site/' + str(site.id) + '/')
    assert response.status_code == HTTPStatus.OK


def test_site_detail_accessible_by_name(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-detail', args=(site.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_detail_uses_correct_template(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-detail', args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_detail.html')


def test_site_create_url_exists_at_desired_location(client):
    response = client.get('/hospital-settings/site/create/')
    assert response.status_code == HTTPStatus.OK


def test_site_create_accessible_by_name(client):
    url = reverse('site-create')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_create_uses_correct_template(client):
    url = reverse('site-create')
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_successfull_create_request_redirects(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    url = reverse('site-create')
    data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': Institution.objects.get(code__exact='ALL_SITES').id,
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert response.status_code == HTTPStatus.FOUND


def test_site_create_with_missing_field(client):
    url = reverse('site-create')
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')


def test_site_update_url_exists_at_desired_location(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    response = client.get('/hospital-settings/site/' + str(site.id) + '/update/')
    assert response.status_code == HTTPStatus.OK


def test_site_update_accessible_by_name(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-update', args=(site.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_site_update_uses_correct_template(client):
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-update', args=(site.id,))
    response = client.get(url)
    assertTemplateUsed(response, 'hospital_settings/site/site_form.html')


def test_site_update_object_displayed(client):
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-update', args=(site.id,))
    response = client.get(url)
    assert 'TEST1_EN' in response.content.decode('utf-8') \
        and 'TEST1_FR' in response.content.decode('utf-8') \
        and 'http://127.0.0.1:8000/hospital-settings/site/1/fr' in response.content.decode('utf-8') \
        and 'http://127.0.0.1:8000/hospital-settings/site/1/en' in response.content.decode('utf-8') \
        and 'TEST1' in response.content.decode('utf-8') \
        and 'TEST1_EN_INST' in response.content.decode('utf-8')


def test_site_successfull_update_request_redirects(client):
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-update', args=(site.id,))
    data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': Institution.objects.get(code__exact='ALL_SITES').id
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert response.status_code == HTTPStatus.FOUND


def test_site_update_with_missing_field(client):
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-update', args=(site.id,))
    data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
    }
    response = client.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    # redirection
    assert 'This field is required' in response.content.decode('utf-8')


def test_site_delete_url_exists_at_desired_location(client):
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    response = client.delete('/hospital-settings/site/' + str(site.id) + '/delete/')
    assert response.status_code == HTTPStatus.FOUND


def test_site_delete_accessible_by_name(client):
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-delete', args=(site.id,))
    response = client.delete(url)
    assert response.status_code == HTTPStatus.FOUND


def test_site_deleted(client):
    Institution.objects.create(name_en='TEST1_EN_INST', name_fr='TEST1_FR', code='ALL_SITES')
    site = Site.objects.create(
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST1',
        institution=Institution.objects.get(code__exact='ALL_SITES')
    )
    url = reverse('site-delete', args=(site.id,))
    client.delete(url)
    assert Institution.objects.filter(pk=site.id).first() is None

# TODO: pagination, ordering, restricted to logged in users
