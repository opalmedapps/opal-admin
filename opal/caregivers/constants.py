"""List of constants for the caregivers app."""
from typing import Final

#: Maximum length verification code for an email_verification.
VERIFICATION_CODE_LENGTH: Final[int] = 6
#: Time delay in seconds for sending email (in seconds).
CODE_RESEND_TIME_DELAY: Final[int] = 10
#: The email verification code timeout in minutes.
EMAIL_VERIFICATION_TIMEOUT: Final[int] = 30
