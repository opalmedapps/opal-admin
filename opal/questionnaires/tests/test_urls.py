from django.urls import resolve, reverse

import pytest

pytestmark = pytest.mark.django_db


def test_exportreports() -> None:
    """Ensure exportreports is defined."""
    assert reverse('questionnaires:exportreports') == '/questionnaires/exportreports/'
    assert resolve('/questionnaires/exportreports/').view_name == 'questionnaires:exportreports'


def test_exportreports_launch() -> None:
    """Ensure exportreports is defined."""
    assert reverse('questionnaires:exportreports-launch') == '/questionnaires/exportreports/launch/'
    assert resolve('/questionnaires/exportreports/launch/').view_name == 'questionnaires:exportreports-launch'
