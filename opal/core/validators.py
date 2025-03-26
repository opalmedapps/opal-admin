"""Module for common validators of specific fields throughout opal system."""
from django.core.validators import RegexValidator

# this ramq validator is an instance of RegexValidator. to be improved later.
ramq_validator = RegexValidator(
    regex='^[a-zA-Z]{4}[0-9]{8}$',
    message='RAMQ format is: LLLLDDDDDDDD - 4 Letters followed by 8 Digits',
)
