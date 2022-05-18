from django.urls import resolve, reverse

import pytest

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


def test_institutions_list() -> None:
    """Ensure institutions list is defined."""
    assert reverse('api:institutions-list') == '/api/institutions/'
    assert resolve('/api/institutions/').view_name == 'api:institutions-list'


def test_institutions_detail(institution: Institution) -> None:
    """Ensure institutions detail is defined."""
    path = f'/api/institutions/{institution.pk}/'
    assert reverse('api:institutions-detail', kwargs={'pk': institution.pk}) == path
    assert resolve(path).view_name == 'api:institutions-detail'


def test_sites_list() -> None:
    """Ensure sites list is defined."""
    assert reverse('api:sites-list') == '/api/sites/'
    assert resolve('/api/sites/').view_name == 'api:sites-list'


def test_sites_detail(site: Site) -> None:
    """Ensure sites detail is defined."""
    path = f'/api/sites/{site.pk}/'
    assert reverse('api:sites-detail', kwargs={'pk': site.pk}) == path
    assert resolve(path).view_name == 'api:sites-detail'
