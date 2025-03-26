from http import HTTPStatus

from django.test import Client
from django.urls.base import reverse

import pytest
from pytest_django.asserts import assertContains, assertTemplateUsed

# Add any future GET-requestable usage statistics pages here for faster test writing
test_url_template_data: list[tuple[str, str]] = [
    (reverse('usage-statistics:reports-group-export'), 'usage_statistics/export_data/export_form.html'),
    (reverse('usage-statistics:reports-individual-export'), 'usage_statistics/export_data/export_form.html'),
]


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_usage_statistics_urls_exist(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page exists at each URL address."""
    response = admin_client.get(url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('url', 'template'), test_url_template_data)
def test_statistics_views_use_correct_template(admin_client: Client, url: str, template: str) -> None:
    """Ensure that a page uses appropriate templates."""
    response = admin_client.get(url)

    assertTemplateUsed(response, template)


def test_usage_statistics_group_export_unauthorized(user_client: Client) -> None:
    """Ensure that an authenticated (not admin) user cannot access the group reports page."""
    response = user_client.get(reverse('usage-statistics:reports-group-export'))

    assertContains(
        response=response,
        text='403 Forbidden',
        status_code=HTTPStatus.FORBIDDEN,
    )


def test_usage_statistics_individual_export_unauthorized(user_client: Client) -> None:
    """Ensure that an authenticated (not admin) user cannot access the individual reports page."""
    response = user_client.get(reverse('usage-statistics:reports-individual-export'))

    assertContains(
        response=response,
        text='403 Forbidden',
        status_code=HTTPStatus.FORBIDDEN,
    )
