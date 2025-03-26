"""Command for detecting outdated registration codes and expire them."""
from datetime import datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from opal.caregivers.constants import REGISTRATION_CODE_EXPIRY
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus


class Command(BaseCommand):
    """Command to find and expire the outdated registration codes outside of the duration `REGISTRATION_CODE_EXPIRY`.

    The variable `REGISTRATION_CODE_EXPIRY` is set in the `constants.py` file.

    The command compares:

        - `creation_date` against current date.
    """

    help = 'expire outdated registration code based on preset duration in constants'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle expiration of registration code with respect to preset duration in the settings.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs:  variable keyword input arguments.
        """
        # get all dates that have passed the allowed duration before expiry
        registrationdate = timezone.make_aware(datetime.today()) - timedelta(hours=REGISTRATION_CODE_EXPIRY)
        registration_codes = RegistrationCode.objects.filter(creation_date__lte=registrationdate)

        for record in registration_codes:
            record.status = RegistrationCodeStatus.EXPIRED
            record.save()
