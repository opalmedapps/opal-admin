"""List of constants for the usage statistics app."""

from typing import Final

from .common import GroupByComponent, GroupReportType

#: Choices for the grouping time intervals
TIME_INTERVAL_GROUPINGS: Final = tuple((item.name, item.value) for item in GroupByComponent)
#: Choices for the group usage statistic report types
GROUP_REPORT_TYPES: Final = tuple((item.name, item.value) for item in GroupReportType)
