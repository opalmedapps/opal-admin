# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import resolve, reverse
from django.views.generic.base import View

import pytest
from pytest_django.asserts import assertURLEqual

from .. import views

TestData = tuple[type, str, str]

# tuple with expected data (view class, url name, url path)
testdata: list[TestData] = [
    (views.GroupUsageStatisticsView, 'usage-statistics:reports-group-export', '/usage-statistics/reports/group/'),
    (
        views.IndividualUsageStatisticsView,
        'usage-statistics:reports-individual-export',
        '/usage-statistics/reports/individual/',
    ),
]


@pytest.mark.parametrize(('view_class', 'url_name', 'url_path'), testdata)
def test_usage_statistics_urls(view_class: type[View], url_name: str, url_path: str) -> None:
    """
    Ensure that usage statistics export URL name resolves to the appropriate URL address.

    It also checks that the URL is served with the correct view.
    """
    assertURLEqual(reverse(url_name), url_path)
    assert resolve(url_path).func.__name__ == view_class.as_view().__name__
