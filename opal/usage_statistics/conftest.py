"""This module is used to provide configuration, fixtures, and plugins for pytest within usage-statistics app."""

import datetime as dt

import pytest

from opal.usage_statistics.forms import GroupUsageStatisticsForm, IndividualUsageStatisticsForm

from .common import GroupByComponent, GroupReportType


@pytest.fixture
def group_usage_stats_form() -> GroupUsageStatisticsForm:
    """Fixture providing data for the `GroupUsageStatisticsForm`.

    Returns:
        `GroupUsageStatisticsForm` object
    """
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'end_date': dt.datetime.now().date(),
        'group_by': GroupByComponent.YEAR.name,
        'report_type': GroupReportType.SUMMARY_REPORT.name,
    }

    return GroupUsageStatisticsForm(data=form_data)


@pytest.fixture
def individual_usage_stats_form() -> IndividualUsageStatisticsForm:
    """Fixture providing data for the `IndividualUsageStatisticsForm`.

    Returns:
        `IndividualUsageStatisticsForm` object
    """
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'end_date': dt.datetime.now().date(),
    }

    return IndividualUsageStatisticsForm(data=form_data)
