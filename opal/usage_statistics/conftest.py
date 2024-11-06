"""This module is used to provide configuration, fixtures, and plugins for pytest within usage-statistics app."""

import datetime as dt

import pytest

from opal.usage_statistics.forms import GroupUsageStatisticsExportForm

from . import constants


@pytest.fixture
def group_usage_stats_form() -> GroupUsageStatisticsExportForm:
    """Fixture providing data for the `GroupUsageStatisticsExportForm`.

    Returns:
        `GroupUsageStatisticsExportForm` object
    """
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'end_date': dt.datetime.now().date(),
        'group_by': constants.GroupByComponent.YEAR.name,
        'report_type': constants.GroupReportType.SUMMARY_REPORT.name,
    }

    return GroupUsageStatisticsExportForm(data=form_data)
