"""Daily command to update the Usage Statistics models.

TODO
- Determine how to capture activity clicked via the Home tab Notifications menu.
These are logged different in PAL than regular Chart activity.
- Ticket to fix the PAL logging of Account language change, bug described in spike doc
- Add last_received and total received fields to PatientDataReceived function for Diagnosis, Announcement?
- Split this command into separate management commands for each usage_statistics report table?
- Abstract the common subquery functionality in _update_patient_data_received to reduce code repetition
"""

from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command to update the daily usage statistics and reporting tables."""

    help = 'Populate Usage statistics and reporting from PatientActivityLog'  # noqa: A003

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle daily calculation of statistics and append to reporting tables.

        Return 'None'.

        Args:
            args: input arguments.
            options:  additional keyword arguments.
        """
        # TODO: implement management command: QSCCD-1951
        print('TODO: implement management command!')
