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


def test_relationships_pending_list() -> None:
    """Ensures a url for relationships exists."""
    url = '/patients/relationships/pending/'
    assert reverse('patients:relationships-pending-list') == url
    assert resolve(url).view_name == 'patients:relationships-pending-list'


def test_caregiver_access_list() -> None:
    """
    Ensure that 'patients:caregiver-access' URL name resolves to the appropriate URL.

    It also checks that the URL is served with the correct view.
    """
    url = '/patients/relationships/search'
    assert reverse('patients:relationships-search') == url
    assert resolve(url).view_name == 'patients:relationships-search'


def test_relationships_pending_update() -> None:
    """Ensures a url for relationships pending access update view exists."""
    url = '/patients/relationships/pending/12/update/'
    assert reverse('patients:relationships-pending-update', kwargs={'pk': 12}) == url
    assert resolve(url).view_name == 'patients:relationships-pending-update'
