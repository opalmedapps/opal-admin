# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import resolve, reverse


def test_relationshiptype_list() -> None:
    """A URL for listing relationship types exists."""
    url = '/patients/relationship-types/'
    assert reverse('patients:relationshiptype-list') == url
    assert resolve(url).view_name == 'patients:relationshiptype-list'


def test_relationshiptype_create() -> None:
    """A URL for creating relationship types exists."""
    url = '/patients/relationship-type/create/'
    assert reverse('patients:relationshiptype-create') == url
    assert resolve(url).view_name == 'patients:relationshiptype-create'


def test_relationshiptype_update() -> None:
    """A URL for updating an existing relationship type exists."""
    url = '/patients/relationship-type/1234/update/'
    assert reverse('patients:relationshiptype-update', kwargs={'pk': 1234}) == url
    assert resolve(url).view_name == 'patients:relationshiptype-update'


def test_relationshiptype_delete() -> None:
    """A URL for deleting an existing relationship type exists."""
    url = '/patients/relationship-type/1234/delete/'
    assert reverse('patients:relationshiptype-delete', kwargs={'pk': 1234}) == url
    assert resolve(url).view_name == 'patients:relationshiptype-delete'


def test_access_request() -> None:
    """A URL for the access request view."""
    url = '/patients/access-request/'
    assert reverse('patients:access-request') == url
    assert resolve(url).view_name == 'patients:access-request'


def test_relationships_pending_list() -> None:
    """Ensures a url for relationships exists."""
    url = '/patients/relationships/'
    assert reverse('patients:relationships-list') == url
    assert resolve(url).view_name == 'patients:relationships-list'


def test_relationships_pending_update() -> None:
    """Ensures a url for relationships pending access update view exists."""
    url = '/patients/relationships/12/'
    assert reverse('patients:relationships-view-update', kwargs={'pk': 12}) == url
    assert resolve(url).view_name == 'patients:relationships-view-update'
