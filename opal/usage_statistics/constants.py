# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""List of constants for the usage statistics app."""

from typing import Final

from .common import GroupByComponent, GroupReportType

#: Choices for the grouping time intervals
TIME_INTERVAL_GROUPINGS: Final = tuple((item.name, item.value) for item in GroupByComponent)
#: Choices for the group usage statistic report types
GROUP_REPORT_TYPES: Final = tuple((item.name, item.value) for item in GroupReportType)
