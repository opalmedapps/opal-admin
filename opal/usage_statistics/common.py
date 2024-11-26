"""List of common entities for the usage statistics app."""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class GroupByComponent(Enum):
    """An enumeration of supported time interval groupings."""

    DAY = _('Day')  # noqa: WPS115
    MONTH = _('Month')  # noqa: WPS115
    YEAR = _('Year')  # noqa: WPS115


class GroupReportType(Enum):
    """An enumeration of group usage statistic report types."""

    SUMMARY_REPORT = _('Grouped registration codes, caregivers, patients, device identifiers')  # noqa: WPS115
    RECEIVED_DATA_REPORT = _('Grouped patients received data')  # noqa: WPS115
    APP_ACTIVITY_REPORT = _('Grouped patient/user app activity')  # noqa: WPS115
