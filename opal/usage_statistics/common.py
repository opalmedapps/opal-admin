"""List of common entities for the usage statistics app."""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class GroupByComponent(Enum):
    """An enumeration of supported time interval groupings."""

    DAY = _('Day')
    MONTH = _('Month')
    YEAR = _('Year')


class GroupReportType(Enum):
    """An enumeration of group usage statistic report types."""

    SUMMARY_REPORT = _('Grouped registration codes, caregivers, patients, device identifiers')
    RECEIVED_DATA_REPORT = _('Grouped patients received data')
    APP_ACTIVITY_REPORT = _('Grouped patient/user app activity')
