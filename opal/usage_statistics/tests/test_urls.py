from django.urls import resolve, reverse


def test_usage_statistics_export_url() -> None:
    """
    Ensure that usage statistics export URL name resolves to the appropriate URL address.

    It also checks that the URL is served with the correct view.
    """
    assert reverse('usage-statistics:data-export') == '/usage-statistics/export/'
    assert resolve('/usage-statistics/export/').view_name == 'usage-statistics:data-export'
