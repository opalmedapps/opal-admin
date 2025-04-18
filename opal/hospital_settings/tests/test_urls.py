# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import resolve, reverse
from django.views.generic.base import View

import pytest
from pytest_django.asserts import assertURLEqual

from .. import views

TestData = tuple[type, str, str]

# tuple with expected data (view class, url name, url path)
testdata: list[TestData] = [
    (views.IndexTemplateView, 'hospital-settings:index', '/hospital-settings/'),
    (views.InstitutionListView, 'hospital-settings:institution-list', '/hospital-settings/institutions/'),
    (
        views.InstitutionCreateUpdateView,
        'hospital-settings:institution-create',
        '/hospital-settings/institution/create/',
    ),
    (views.SiteListView, 'hospital-settings:site-list', '/hospital-settings/sites/'),
    (views.SiteCreateUpdateView, 'hospital-settings:site-create', '/hospital-settings/site/create/'),
]


@pytest.mark.parametrize(('view_class', 'url_name', 'url_path'), testdata)
def test_hospital_settings_urls(view_class: type[View], url_name: str, url_path: str) -> None:
    """
    Ensure that an URL name resolves to the appropriate URL address.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(reverse(url_name), url_path)
    assert resolve(url_path).func.__name__ == view_class.as_view().__name__


# INSTITUTIONS


def test_institution_update_url_is_resolved() -> None:
    """
    Ensure that `institution-update` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:institution-update', args=[42]),
        '/hospital-settings/institution/42/update/',
    )
    path_name = resolve('/hospital-settings/institution/42/update/').func.__name__
    assert path_name == views.InstitutionCreateUpdateView.as_view().__name__


def test_institution_delete_url_is_resolved() -> None:
    """
    Ensure that `institution-delete` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:institution-delete', args=[42]),
        '/hospital-settings/institution/42/delete/',
    )
    path_name = resolve('/hospital-settings/institution/42/delete/').func.__name__
    assert path_name == views.InstitutionDeleteView.as_view().__name__


# SITES


def test_site_update_url_is_resolved() -> None:
    """
    Ensure that `site-update` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:site-update', args=[42]),
        '/hospital-settings/site/42/update/',
    )
    path_name = resolve('/hospital-settings/site/42/update/').func.__name__
    assert path_name == views.SiteCreateUpdateView.as_view().__name__


def test_site_delete_url_is_resolved() -> None:
    """
    Ensure that `site-delete` URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(
        reverse('hospital-settings:site-delete', args=[42]),
        '/hospital-settings/site/42/delete/',
    )
    path_name = resolve('/hospital-settings/site/42/delete/').func.__name__
    assert path_name == views.SiteDeleteView.as_view().__name__
