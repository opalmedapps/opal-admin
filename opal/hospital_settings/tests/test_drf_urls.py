from django.urls import resolve, reverse


def test_institutions_list() -> None:
    """Ensure institutions list is defined."""
    assert reverse('api:institutions-list') == '/api/institutions/'
    assert resolve('/api/institutions/').view_name == 'api:institutions-list'


def test_sites_list() -> None:
    """Ensure sites list is defined."""
    assert reverse('api:sites-list') == '/api/sites/'
    assert resolve('/api/sites/').view_name == 'api:sites-list'
