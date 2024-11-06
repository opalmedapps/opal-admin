"""List of constants for the usage statistics app."""

from enum import Enum
from typing import Final

from django.utils.translation import gettext


class GroupByComponent(Enum):
    """An enumeration of supported time interval groupings."""

    DAY = gettext('Day')  # noqa: WPS115
    MONTH = gettext('Month')  # noqa: WPS115
    YEAR = gettext('Year')  # noqa: WPS115


class GroupReportType(Enum):
    """An enumeration of group usage statistic report types."""

    SUMMARY_REPORT = gettext('Grouped registration codes, caregivers, patients, device identifiers')  # noqa: WPS115
    RECEIVED_DATA_REPORT = gettext('Grouped patients received data')  # noqa: WPS115
    APP_ACTIVITY_REPORT = gettext('Grouped patient/user app activity')  # noqa: WPS115


#: Choices for the grouping time intervals
TIME_INTERVAL_GROUPINGS: Final = tuple((item.name, item.value) for item in GroupByComponent)
#: Choices for the group usage statistic report types
GROUP_REPORT_TYPES: Final = tuple((item.name, item.value) for item in GroupReportType)
