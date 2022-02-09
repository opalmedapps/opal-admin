from django.test import Client
from django.urls.base import reverse

import pytest

from ..models import Institution, Site

TEST_HOSPITAL = 'Test Hospital'

pytestmark = pytest.mark.django_db


def test_location_string() -> None:
    """This test ensures the __str__ method is defined."""
    # Location is abstract and cannot be instantiated directly
    institution = Institution(name=TEST_HOSPITAL, code='TH')

    assert str(institution) == TEST_HOSPITAL


def test_institution_ordered() -> None:
    """This test ensures that the institutions are ordered by name."""
    Institution.objects.create(name=TEST_HOSPITAL, code='TH')
    Institution.objects.create(name='ATest Hospital', code='TH2')

    first = Institution.objects.all()[0]

    assert first.name == 'ATest Hospital'


def test_site_ordered() -> None:
    """This test ensures that the sites are ordered by name."""
    institution = Institution.objects.create(name=TEST_HOSPITAL, code='TH')

    Site.objects.create(name='Test Site', code='TST', institution=institution)
    Site.objects.create(name='ATest Site', code='TST2', institution=institution)

    first = Site.objects.all()[0]

    assert first.name == 'ATest Site'


def test_institution_deleted(client: Client, institution: Institution) -> None:
    """This test ensures that an institution is deleted from the database."""
    url = reverse('institution-delete', args=(institution.id,))
    client.delete(url)
    assert Institution.objects.filter(pk=institution.id).first() is None


def test_site_deleted(client: Client) -> None:
    """This test ensures that a site is deleted from the database."""
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
    client.delete(url)
    assert Institution.objects.filter(pk=site.id).first() is None
