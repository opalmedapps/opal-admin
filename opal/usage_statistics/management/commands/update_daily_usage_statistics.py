"""Command for updating the `DailyUserAppActivity` model on daily basis.

TODO
- Determine how to capture activity clicked via the Home tab Notifications menu.
These are logged different in PAL than regular Chart activity.
- Add last_received and total received fields to PatientDataReceived function for Diagnosis, Announcement?
"""

import datetime as dt
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from django_stubs_ext.aliases import ValuesQuerySet

from opal.caregivers.models import CaregiverProfile
from opal.legacy.models import LegacyPatientActivityLog
from opal.patients.models import Patient, Relationship, RelationshipStatus
from opal.usage_statistics.models import DailyPatientDataReceived, DailyUserAppActivity
from opal.users.models import User


class Command(BaseCommand):
    """
    Command to update the daily app activity statistics per user and patient (e.g., `DailyUserAppActivity` model).

    The command is added to the crontab (e.g., `docker/crontab`) and called daily at 5am EST.
    """

    help = 'Populate the daily app activity statistics from PatientActivityLog to DailyUserAppActivity'  # noqa: A003

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument(
            '--force-delete',
            action='store_true',
            default=False,
            help='Force deleting existing activity data first before initializing (default: false)',
        )
        parser.add_argument(
            '--today',
            action='store_true',
            default=False,
            help='Calculate the usage statistics for the current day between midnight and NOW() (default: false)',
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Process daily application activity statistics and populate the values to the `DailyUserAppActivity`.

        By default, the command calculates the usage statistics for the previous complete day (e.g., 00:00:00-23:59:59).

        Args:
            args: input arguments
            options:  additional keyword arguments
        """
        # Convenience CL arg for testing; DO NOT USE IN PROD!
        if options['force_delete']:
            self.stdout.write(self.style.WARNING('Deleting existing usage statistics data'))
            confirm = input(
                'Are you sure you want to do this?\n'
                + '\n'
                + "Type 'yes' to continue, or 'no' to cancel: ",
            )

            if confirm != 'yes':
                self.stdout.write('Usage statistics update is cancelled')
                return

            DailyUserAppActivity.objects.all().delete()
            DailyPatientDataReceived.objects.all().delete()

        # By default the command extract the statistics for the previous day
        days_delta = 1

        # Optional today parameter for calculating app statistics for the current day between 00:00:00 and 23:59:59
        if options['today']:
            self.stdout.write(self.style.WARNING('Calculating usage statistics for today'))
            days_delta = 0

        # Set the default query time period for the previous complete day (e.g., between 00:00:00 and 23:59:59)
        start_datetime_period = dt.datetime.combine(
            timezone.now() - dt.timedelta(days=days_delta),
            dt.datetime.min.time(),
            timezone.get_current_timezone(),
        )
        end_datetime_period = dt.datetime.combine(
            start_datetime_period,
            dt.datetime.max.time(),
            timezone.get_current_timezone(),
        )

        activities = LegacyPatientActivityLog.objects.get_aggregated_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        )

        self._populate_user_app_activities(activities=activities)

        self.stdout.write(self.style.SUCCESS('Successfully populated statistics data to DailyUserAppActivity model'))

    def _populate_user_app_activities(
        self,
        activities: ValuesQuerySet['LegacyPatientActivityLog', dict[str, Any]],
    ) -> None:
        """Query from PatientActivityLog to generate daily user/patient app activity.

        Args:
            activities: `LegacyPatientActivityLog` records to be populated to `DailyUserAppActivity`
        """
        daily_app_activities = []

        for activity in activities:
            user = User.objects.filter(username=activity['username']).first()
            patient_data_owner = Patient.objects.filter(legacy_id=activity['target_patient_id']).first()
            caregiver_profile = CaregiverProfile.objects.filter(user=user).first()

            activity.pop('target_patient_id')
            activity.pop('username')

            daily_app_activities.append(
                DailyUserAppActivity(
                    **activity,
                    action_by_user=user,
                    # Feedback: It makes sense to filter only confirmed relationships... I think?
                    user_relationship_to_patient=Relationship.objects.filter(
                        patient=patient_data_owner,
                        caregiver=caregiver_profile,
                        status=RelationshipStatus.CONFIRMED,
                    ).first(),
                    patient=patient_data_owner,
                    date_added=timezone.now().date(),
                ),
            )

        DailyUserAppActivity.objects.bulk_create(daily_app_activities)
