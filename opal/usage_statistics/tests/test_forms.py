import datetime as dt
import json

from ..common import GroupByComponent, GroupReportType
from ..forms import GroupUsageStatisticsExportForm


def test_group_usage_stats_form_is_valid(group_usage_stats_form: GroupUsageStatisticsExportForm) -> None:
    """Ensure that the GroupUsageStatisticsExportForm is valid."""
    assert group_usage_stats_form.is_valid()


def test_group_stats_form_missing_start_date() -> None:
    """Ensure that the GroupUsageStatisticsExportForm checks for missing start date."""
    form_data = {
        'end_date': dt.datetime.now().date(),
        'group_by': GroupByComponent.YEAR.name,
        'report_type': GroupReportType.APP_ACTIVITY_REPORT.name,
    }
    form = GroupUsageStatisticsExportForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'start_date': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_missing_end_date() -> None:
    """Ensure that the GroupUsageStatisticsExportForm checks for missing end date."""
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'group_by': GroupByComponent.YEAR.name,
        'report_type': GroupReportType.RECEIVED_DATA_REPORT.name,
    }
    form = GroupUsageStatisticsExportForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'end_date': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_missing_group_by() -> None:
    """Ensure that the GroupUsageStatisticsExportForm checks for missing group by."""
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'end_date': dt.datetime.now().date(),
        'report_type': GroupReportType.SUMMARY_REPORT.name,
    }
    form = GroupUsageStatisticsExportForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'group_by': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_missing_report_type() -> None:
    """Ensure that the GroupUsageStatisticsExportForm checks for missing report type."""
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'end_date': dt.datetime.now().date(),
        'group_by': GroupByComponent.YEAR.name,
    }
    form = GroupUsageStatisticsExportForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'report_type': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_start_later_than_end() -> None:
    """Ensure GroupUsageStatisticsExportForm checks that start date is not later than end date."""
    form_data = {
        'start_date': dt.datetime.now().date(),
        'end_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'group_by': GroupByComponent.YEAR.name,
        'report_type': GroupReportType.APP_ACTIVITY_REPORT.name,
    }
    form = GroupUsageStatisticsExportForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        '__all__': [{
            'message': 'Start date cannot be later than end date.',
            'code': '',
        }],
    })
