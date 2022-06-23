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
