"""List of constants for the patients app."""
from enum import Enum
from typing import Final

from django.utils.translation import gettext_lazy as _


class MedicalCard(Enum):
    """An enumeration of supported medical card types."""

    RAMQ = _('Medicare Card (RAMQ)')  # noqa: WPS115
    MRN = _('Hospital Card (MRN)')  # noqa: WPS115


class UserType(Enum):
    """An enumeration of user types."""

    NEW = _('New Opal User')  # noqa: WPS115
    EXISTING = _('Existing Opal User')  # noqa: WPS115


#: Choices for the type of the medical cards
MEDICAL_CARDS: Final = tuple((item.name, item.value) for item in MedicalCard)
#: Choices for the type of user
USER_TYPES: Final = tuple((item.name, item.value) for item in UserType)

#: Maximum possible patient age for a relationship.
RELATIONSHIP_MAX_AGE: Final = 150
#: Minimum possible patient age for a relationship.
RELATIONSHIP_MIN_AGE: Final = 0
#: Choices for the type of users
# TODO: we might refactor this constant name for more clarity
TYPE_USERS: Final = ((0, _('New Opal User')), (1, _('Existing Opal User')))
#: The value to be replaced in the original datetime.
RELATIVE_YEAR_VALUE: Final = 2
#: New user for the requestor type.
NEW_USER: Final = 0
#: Existing user for the requestor type.
EXISTING_USER: Final = 1
#: Random uuid hexadecimal string length for the caregiver username.
USERNAME_LENGTH: Final = 30
#: QR code dimension
QR_CODE_BOX_SIZE: Final = 10
