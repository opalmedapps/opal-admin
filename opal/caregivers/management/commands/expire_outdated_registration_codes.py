"""Command for detecting outdated new registration codes and expire them."""
from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from opal.caregivers.constants import REGISTRATION_CODE_EXPIRY
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus


class Command(BaseCommand):
    """Command to find and expire the outdated registration codes outside of the duration `REGISTRATION_CODE_EXPIRY`.

    The variable `REGISTRATION_CODE_EXPIRY` is set in the `constants.py` file.

    The command compares the registration code's `created_at` with the current date and time.

    """

    help = 'expire outdated registration code based on preset duration in constants'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle expiration of `NEW` registration code with respect to preset duration in the settings.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs:  variable keyword input arguments.
        """
        # get all dates that have passed the allowed duration before expiry
        expiration_datetime = timezone.now() - timedelta(hours=REGISTRATION_CODE_EXPIRY)
        registration_codes = RegistrationCode.objects.filter(
            status=RegistrationCodeStatus.NEW,
            created_at__lte=expiration_datetime,
        ).update(status=RegistrationCodeStatus.EXPIRED)

        self.stdout.write(
            f'Number of expired registration codes: {registration_codes}',
        )
