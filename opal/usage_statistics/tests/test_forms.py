from ..forms import GroupUsageStatisticsExportForm


def test_group_usage_stats_form_is_valid(group_usage_stats_form: GroupUsageStatisticsExportForm) -> None:
    """Ensure that the GroupUsageStatisticsExportForm is valid."""
    assert group_usage_stats_form.is_valid()
