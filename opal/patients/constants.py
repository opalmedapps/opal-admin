"""List of constants for the patients app."""
from typing import Final

#: Maximum possible patient age for a relationship.
RELATIONSHIP_MAX_AGE: Final = 150
#: Minimum possible patient age for a relationship.
RELATIONSHIP_MIN_AGE: Final = 0
#: Choices for the type of the medical cards
MEDICAL_CARDS: Final = (('mrn', 'MRN'), ('ramq', 'RAMQ'))
