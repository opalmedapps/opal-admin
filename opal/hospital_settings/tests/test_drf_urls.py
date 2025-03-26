from django.urls import resolve, reverse

import pytest

from .. import factories

pytestmark = pytest.mark.django_db


def test_institutions_list() -> None:
    """Ensure institutions list is defined."""
    assert reverse('api:institutions-list') == '/api/institutions/'
    assert resolve('/api/institutions/').view_name == 'api:institutions-list'


def test_institutions_detail() -> None:
    """Ensure institutions detail is defined."""
    institution = factories.Institution()

    path = f'/api/institutions/{institution.pk}/'
    assert reverse('api:institutions-detail', kwargs={'pk': institution.pk}) == path
    assert resolve(path).view_name == 'api:institutions-detail'


def test_retrieve_terms_of_use() -> None:
    """Ensure retrieve terms of use is defined."""
    institution = factories.Institution()

    path = f'/api/institutions/{institution.pk}/terms-of-use/'
    assert reverse('api:institutions-terms-of-use', kwargs={'pk': institution.pk}) == path
    assert resolve(path).view_name == 'api:institutions-terms-of-use'


def test_sites_list() -> None:
    """Ensure sites list is defined."""
    assert reverse('api:sites-list') == '/api/sites/'
    assert resolve('/api/sites/').view_name == 'api:sites-list'


def test_sites_detail() -> None:
    """Ensure sites detail is defined."""
    site = factories.Site()

    path = f'/api/sites/{site.pk}/'
    assert reverse('api:sites-detail', kwargs={'pk': site.pk}) == path
    assert resolve(path).view_name == 'api:sites-detail'
