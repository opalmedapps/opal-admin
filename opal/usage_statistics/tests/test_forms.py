import datetime as dt
import json

from ..common import GroupByComponent, GroupReportType
from ..forms import GroupUsageStatisticsForm, IndividualUsageStatisticsForm


def test_group_usage_stats_form_is_valid(group_usage_stats_form: GroupUsageStatisticsForm) -> None:
    """Ensure that the GroupUsageStatisticsForm is valid."""
    assert group_usage_stats_form.is_valid()


def test_group_stats_form_missing_start_date() -> None:
    """Ensure that the GroupUsageStatisticsForm checks for missing start date."""
    form_data = {
        'end_date': dt.datetime.now().date(),
        'group_by': GroupByComponent.YEAR.name,
        'report_type': GroupReportType.APP_ACTIVITY_REPORT.name,
    }
    form = GroupUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'start_date': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_missing_end_date() -> None:
    """Ensure that the GroupUsageStatisticsForm checks for missing end date."""
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'group_by': GroupByComponent.YEAR.name,
        'report_type': GroupReportType.RECEIVED_DATA_REPORT.name,
    }
    form = GroupUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'end_date': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_missing_group_by() -> None:
    """Ensure that the GroupUsageStatisticsForm checks for missing group by."""
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'end_date': dt.datetime.now().date(),
        'report_type': GroupReportType.SUMMARY_REPORT.name,
    }
    form = GroupUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'group_by': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_missing_report_type() -> None:
    """Ensure that the GroupUsageStatisticsForm checks for missing report type."""
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'end_date': dt.datetime.now().date(),
        'group_by': GroupByComponent.YEAR.name,
    }
    form = GroupUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'report_type': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_group_stats_form_start_later_than_end() -> None:
    """Ensure GroupUsageStatisticsForm checks that start date is not later than end date."""
    form_data = {
        'start_date': dt.datetime.now().date(),
        'end_date': dt.datetime.now().date() - dt.timedelta(days=7),
        'group_by': GroupByComponent.YEAR.name,
        'report_type': GroupReportType.APP_ACTIVITY_REPORT.name,
    }
    form = GroupUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        '__all__': [{
            'message': 'Start date cannot be later than end date.',
            'code': '',
        }],
    })


def test_individual_stats_form_empty_is_valid() -> None:
    """Ensure that empty IndividualUsageStatisticsForm is valid."""
    form = IndividualUsageStatisticsForm(data={})
    assert form.is_valid()


def test_individual_usage_stats_form_is_valid(individual_usage_stats_form: IndividualUsageStatisticsForm) -> None:
    """Ensure that the IndividualUsageStatisticsForm is valid."""
    assert individual_usage_stats_form.is_valid()


def test_individual_stats_form_missing_start_date() -> None:
    """Ensure that the IndividualUsageStatisticsForm checks for missing start date."""
    form_data = {
        'end_date': dt.datetime.now().date(),
    }
    form = IndividualUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'start_date': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_individual_stats_form_missing_end_date() -> None:
    """Ensure that the IndividualUsageStatisticsForm checks for missing end date."""
    form_data = {
        'start_date': dt.datetime.now().date() - dt.timedelta(days=7),
    }
    form = IndividualUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        'end_date': [{
            'message': 'This field is required.',
            'code': 'required',
        }],
    })


def test_individual_stats_form_start_later_than_end() -> None:
    """Ensure IndividualUsageStatisticsForm checks that start date is not later than end date."""
    form_data = {
        'start_date': dt.datetime.now().date(),
        'end_date': dt.datetime.now().date() - dt.timedelta(days=7),
    }
    form = IndividualUsageStatisticsForm(data=form_data)

    assert not form.is_valid()
    assert form.errors.as_json() == json.dumps({
        '__all__': [{
            'message': 'Start date cannot be later than end date.',
            'code': '',
        }],
    })
