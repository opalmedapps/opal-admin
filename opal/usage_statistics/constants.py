"""List of constants for the usage statistics app."""

from enum import Enum
from typing import Final

from django.utils.translation import gettext_lazy as _


class TimeIntervalGrouping(Enum):
    """An enumeration of supported time interval groupings."""

    DAY = _('Day')  # noqa: WPS115
    MONTH = _('Month')  # noqa: WPS115
    YEAR = _('Year')  # noqa: WPS115


class GroupReportType(Enum):
    """An enumeration of group usage statistic report types."""

    SUMMARY_REPORT = _('Grouped registration codes, caregivers, patients, device identifiers')  # noqa: WPS115
    RECEIVED_DATA_REPORT = _('Grouped patients received data')  # noqa: WPS115
    APP_ACTIVITY_REPORT = _('Grouped patient/user app activity')  # noqa: WPS115


#: Choices for the grouping time intervals
TIME_INTERVAL_GROUPINGS: Final = tuple((item.name, item.value) for item in TimeIntervalGrouping)
#: Choices for the group usage statistic report types
GROUP_REPORT_TYPES: Final = tuple((item.name, item.value) for item in GroupReportType)
