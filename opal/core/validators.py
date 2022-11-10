"""Module for common validators of specific fields throughout opal system."""
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

validate_ramq = RegexValidator(
    regex='^[A-Z]{4}[0-9]{8}$',
    message=_('Enter a valid RAMQ number consisting of 4 letters followed by 8 digits'),
)

validate_phone_number = RegexValidator(
    regex=r'^\+[1-9]\d{6,14}(x\d{1,5})?$',
    message=_(
        'Enter a valid phone number having the format: +<countryCode><phoneNumber> '
        + '(for example +15141234567) with an optional extension "x123"',
    ),
)
