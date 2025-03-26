"""Module for common validators of specific fields throughout opal system."""
from django.core.validators import RegexValidator

#: this ramq validator is an instance of RegexValidator. to be improved later.
ramq_validator = RegexValidator(r'[a-zA-Z]{4}\d{8}', 'RAMQ should be 4 letters followed by 8 digits')

