from django.test import Client
from django.urls import reverse

import pytest
from bs4 import BeautifulSoup

pytestmark = pytest.mark.django_db


def menu_groups(content: bytes) -> list[str]:
    soup = BeautifulSoup(content, 'html.parser')
    menus = soup.select('nav ul li button.btn-toggle')

    return [menu_group.text.strip() for menu_group in menus]


def test_no_permissions(user_client: Client) -> None:
    response = user_client.get(reverse('start'), follow=True)

    groups = menu_groups(response.content)

    assert groups == ['Home']
