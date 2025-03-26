from django.urls import resolve, reverse


def test_health_data_ui_url_exists() -> None:
    """A URL for wearables UI page exists."""
    url = '/health_data/1/quantity-samples/'
    assert reverse('health_data:health-data-ui', kwargs={'id': 1}) == url
    assert resolve(url).view_name == 'health_data:health-data-ui'
