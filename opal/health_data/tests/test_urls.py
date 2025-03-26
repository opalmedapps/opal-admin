from uuid import uuid4

from django.urls import resolve, reverse


def test_health_data_ui_url_exists() -> None:
    """A URL for wearables UI page exists."""
    uuid = uuid4()
    url = '/health-data/{uuid}/quantity-samples/'.format(uuid=uuid)
    assert reverse('health_data:health-data-ui', kwargs={'uuid': uuid}) == url
    assert resolve(url).view_name == 'health_data:health-data-ui'
