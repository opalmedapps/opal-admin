"""Module for common validators of specific fields throughout opal system."""
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

validate_ramq = RegexValidator(
    regex='^[A-Z]{4}[0-9]{8}$',
    message=_('Enter a valid RAMQ number consisting of 4 letters followed by 8 digits'),
)
