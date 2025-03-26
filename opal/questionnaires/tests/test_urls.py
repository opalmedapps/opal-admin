from django.urls import resolve, reverse

import pytest

pytestmark = pytest.mark.django_db


def test_reports_list() -> None:
    """Ensure exportreports list is defined."""
    assert reverse('questionnaires:reports-list') == '/questionnaires/reports/'
    assert resolve('/questionnaires/reports/').view_name == 'questionnaires:reports-list'


def test_reports_filter() -> None:
    """Ensure exportreports query is defined."""
    assert reverse('questionnaires:reports-filter') == '/questionnaires/reports/filter/'
    assert resolve('/questionnaires/reports/filter/').view_name == 'questionnaires:reports-filter'


def test_reports_detail() -> None:
    """Ensure exportreports view report is defined."""
    assert reverse('questionnaires:reports-detail') == '/questionnaires/reports/detail/'
    assert resolve('/questionnaires/reports/detail/').view_name == 'questionnaires:reports-detail'


def test_reports_downloadcsv() -> None:
    """Ensure exportreports downloadcsv is defined."""
    assert reverse('questionnaires:reports-downloadcsv') == '/questionnaires/reports/downloadcsv/'
    assert resolve('/questionnaires/reports/downloadcsv/').view_name == 'questionnaires:reports-downloadcsv'


def test_reports_downloadxlsx() -> None:
    """Ensure exportreports downloadxlsx is defined."""
    assert reverse('questionnaires:reports-downloadxlsx') == '/questionnaires/reports/downloadxlsx/'
    assert resolve('/questionnaires/reports/downloadxlsx/').view_name == 'questionnaires:reports-downloadxlsx'
