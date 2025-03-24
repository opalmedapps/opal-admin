# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module for common validators of specific fields throughout opal system."""

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

validate_ramq = RegexValidator(
    regex='^[A-Z]{4}[0-9]{8}$',
    message=_('Enter a valid RAMQ number consisting of 4 letters followed by 8 digits'),
)
