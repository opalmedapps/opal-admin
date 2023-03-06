"""List of constants for the caregivers app."""
from typing import Final

#: Maximum length verification code for an email_verification.
VERIFICATION_CODE_LENGTH: Final[int] = 6
#: Time delay in seconds for sending email.
TIME_DELAY: Final[int] = 10
#: Time allowed to keep registration code active before they are expired (in hours).
REGISTRATION_CODE_EXPIRY: Final[int] = 72
