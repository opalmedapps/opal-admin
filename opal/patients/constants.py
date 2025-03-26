"""List of constants for the patients app."""
from typing import Final

from django.utils.translation import gettext_lazy as _

#: Maximum possible patient age for a relationship.
RELATIONSHIP_MAX_AGE: Final = 150
#: Minimum possible patient age for a relationship.
RELATIONSHIP_MIN_AGE: Final = 0
#: Choices for the type of the medical cards
MEDICAL_CARDS: Final = (('mrn', _('Medical Record Number (MRN)')), ('ramq', _('Medicare Card Number (RAMQ)')))
#: Choices for the type of users
# TODO: we might refactor this constant name for more clarity
TYPE_USERS: Final = ((0, _('New Opal User')), (1, _('Existing Opal User')))
