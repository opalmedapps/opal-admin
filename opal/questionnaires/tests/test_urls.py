from django.urls import resolve, reverse

import pytest

pytestmark = pytest.mark.django_db


def test_exportreports_list() -> None:
    """Ensure exportreports list is defined."""
    assert reverse('questionnaires:exportreports-list') == '/questionnaires/exportreports-list/'
    assert resolve('/questionnaires/exportreports-list/').view_name == 'questionnaires:exportreports-list'


def test_exportreports_query() -> None:
    """Ensure exportreports query is defined."""
    assert reverse('questionnaires:exportreports-query') == '/questionnaires/exportreports-query/'
    assert resolve('/questionnaires/exportreports-query/').view_name == 'questionnaires:exportreports-query'


def test_exportreports_viewreport() -> None:
    """Ensure exportreports view report is defined."""
    assert reverse('questionnaires:exportreports-viewreport') == '/questionnaires/exportreports-viewreport/'
    assert resolve('/questionnaires/exportreports-viewreport/').view_name == 'questionnaires:exportreports-viewreport'


def test_exportreports_downloadcsv() -> None:
    """Ensure exportreports downloadcsv is defined."""
    assert reverse('questionnaires:exportreports-downloadcsv') == '/questionnaires/exportreports-downloadcsv/'
    assert resolve('/questionnaires/exportreports-downloadcsv/').view_name == 'questionnaires:exportreports-downloadcsv'


def test_exportreports_downloadxlsx() -> None:
    """Ensure exportreports downloadxlsx is defined."""
    assert reverse('questionnaires:exportreports-downloadxlsx') == '/questionnaires/exportreports-downloadxlsx/'
    assert resolve('/questionnaires/exportreports-downloadxlsx/').view_name == 'questionnaires:exportreports-downloadxlsx'  # noqa: E501
