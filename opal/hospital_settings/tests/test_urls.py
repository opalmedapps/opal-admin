from typing import List, Tuple

from django.urls.base import resolve, reverse

import pytest
from pytest_django.asserts import assertURLEqual

from .. import views
from ..models import Institution, Site

pytestmark = pytest.mark.django_db

# tuple with expected data (view class, url name, url path)
testdata: List[Tuple] = [
    (views.IndexTemplateView, 'hospital-settings:index', '/hospital-settings/'),
    (views.InstitutionListView, 'hospital-settings:institution-list', '/hospital-settings/institutions/'),
    (views.InstitutionCreateView, 'hospital-settings:institution-create', '/hospital-settings/institution/create/'),
    (views.SiteListView, 'hospital-settings:site-list', '/hospital-settings/sites/'),
    (views.SiteCreateView, 'hospital-settings:site-create', '/hospital-settings/site/create/'),
]


@pytest.mark.parametrize(('view_class', 'path_name', 'url'), testdata)
def test_hospital_settings_urls(view_class, path_name, url):
    """
    This test ensures that an URL name resolves to the appropriate URL address.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(reverse(path_name), url)
    assert resolve(url).func.__name__ == view_class.as_view().__name__


# INSTITUTIONS

def test_institution_detail_url_is_resolved(institution: Institution) -> None:
    """
    This test ensures that `institution-detail` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:institution-detail', args=[institution.id]),
        '/hospital-settings/institution/{0}/'.format(institution.id),
    )
    path_name = resolve('/hospital-settings/institution/{0}/'.format(institution.id)).func.__name__
    assert path_name == views.InstitutionDetailView.as_view().__name__


def test_institution_update_url_is_resolved(institution: Institution) -> None:
    """
    This test ensures that `institution-update` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:institution-update', args=[institution.id]),
        '/hospital-settings/institution/{0}/update/'.format(institution.id),
    )
    path_name = resolve('/hospital-settings/institution/{0}/update/'.format(institution.id)).func.__name__
    assert path_name == views.InstitutionUpdateView.as_view().__name__


def test_institution_delete_url_is_resolved(institution: Institution) -> None:
    """
    This test ensures that `institution-delete` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:institution-delete', args=[institution.id]),
        '/hospital-settings/institution/{0}/delete/'.format(institution.id),
    )
    path_name = resolve('/hospital-settings/institution/{0}/delete/'.format(institution.id)).func.__name__
    assert path_name == views.InstitutionDeleteView.as_view().__name__


# SITES

def test_site_detail_url_is_resolved(site: Site) -> None:
    """
    This test ensures that `site-detail` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:site-detail', args=[site.id]),
        '/hospital-settings/site/{0}/'.format(site.id),
    )
    path_name = resolve('/hospital-settings/site/{0}/'.format(site.id)).func.__name__
    assert path_name == views.SiteDetailView.as_view().__name__


def test_site_update_url_is_resolved(site: Site) -> None:
    """
    This test ensures that `site-update` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:site-update', args=[site.id]),
        '/hospital-settings/site/{0}/update/'.format(site.id),
    )
    path_name = resolve('/hospital-settings/site/{0}/update/'.format(site.id)).func.__name__
    assert path_name == views.SiteUpdateView.as_view().__name__


def test_site_delete_url_is_resolved(site: Site) -> None:
    """
    This test ensures that `site-delete` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:site-delete', args=[site.id]),
        '/hospital-settings/site/{0}/delete/'.format(site.id),
    )
    path_name = resolve('/hospital-settings/site/{0}/delete/'.format(site.id)).func.__name__
    assert path_name == views.SiteDeleteView.as_view().__name__
