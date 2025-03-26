"""Command for updating the `DailyUserAppActivity` and `DailyUserPatientActivity` models on daily basis.

TODO
- Determine how to capture activity clicked via the Home tab Notifications menu.
These are logged different in PAL than regular Chart activity.
- Add last_received and total received fields to PatientDataReceived function for Diagnosis, Announcement?
"""

import datetime as dt
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import models, transaction
from django.utils import timezone

from opal.caregivers.models import CaregiverProfile
from opal.legacy.models import LegacyPatientActivityLog
from opal.patients.models import Patient, Relationship, RelationshipStatus
from opal.usage_statistics.models import DailyUserAppActivity, DailyUserPatientActivity
from opal.users.models import User


class Command(BaseCommand):
    """
    Command to update the daily app activity statistics per user and patient.

    The command populates `DailyUserAppActivity` and `DailyUserPatientActivity` models.

    It is added to the crontab (e.g., `docker/crontab`) and called daily at 5am EST.
    """

    help = 'Populate the daily app activity statistics per user and patient from PatientActivityLog'  # noqa: A003

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
        Populate daily application activity statistics to the `DailyUserAppActivity` and `DailyUserPatientActivity`.

        By default, the command calculates the usage statistics for the previous complete day (e.g., 00:00:00-23:59:59).

        Args:
            args: input arguments
            options:  additional keyword arguments
        """
        # Convenience CL arg for testing; DO NOT USE IN PROD!
        if options['force_delete']:
            self._delete_stored_statistics()

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

        self._populate_user_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        )

        self._populate_patient_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        )

        self.stdout.write(self.style.SUCCESS(
            'Successfully populated daily statistics data',
        ))

    def _populate_user_app_activities(
        self,
        start_datetime_period: dt.datetime,
        end_datetime_period: dt.datetime,
    ) -> None:
        """Create daily users' application activity statistics records in `DailyUserAppActivity` model.

        Args:
            start_datetime_period: the beginning of the time period of users' app activities being extracted
            end_datetime_period: the end of the time period of users' app activities being extracted
        """
        # NOTE! The date_added indicates the date when the activity statistics were populated.
        # It is not the date when the activities were made.
        date_added = timezone.now().date()
        users = User.objects.all().values('id', 'username')
        users_dict = {user['username']: user['id'] for user in users}

        activities = LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        ).annotate(
            date_added=models.Value(date_added),
        )

        for activity in activities:
            activity['action_by_user'] = User(id=users_dict[activity['username']])
            activity.pop('username')

        DailyUserAppActivity.objects.bulk_create(
            DailyUserAppActivity(**activity_data) for activity_data in activities
        )

    def _populate_patient_app_activities(
        self,
        start_datetime_period: dt.datetime,
        end_datetime_period: dt.datetime,
    ) -> None:
        """Create daily user-patient application activity statistics records in `DailyUserPatientActivity` model.

        Args:
            start_datetime_period: the beginning of the time period of patients' app activities being extracted
            end_datetime_period: the end of the time period of patients' app activities being extracted
        """
        # NOTE! The date_added indicates the date when the activity statistics were populated.
        # It is not the date when the activities were made.
        date_added = timezone.now().date()
        activities = LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        ).annotate(
            date_added=models.Value(date_added),
        )

        for activity in activities:
            activity['action_by_user'] = User.objects.filter(username=activity['username']).first()
            activity['patient'] = Patient.objects.filter(legacy_id=activity['target_patient_id']).first()
            caregiver_profile = CaregiverProfile.objects.filter(user=activity['action_by_user']).first()
            # Feedback: It makes sense to filter only confirmed relationships... I think?
            activity['user_relationship_to_patient'] = Relationship.objects.filter(
                patient=activity['patient'],
                caregiver=caregiver_profile,
                status=RelationshipStatus.CONFIRMED,
            ).first()

            activity.pop('target_patient_id')
            activity.pop('username')

        DailyUserPatientActivity.objects.bulk_create(
            DailyUserPatientActivity(**activity_data) for activity_data in activities
        )

    def _delete_stored_statistics(self) -> None:
        """Delete daily application activity statistics data.

        The records deleted from the `DailyUserAppActivity`, `DailyUserPatientActivity` models.
        """
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
        DailyUserPatientActivity.objects.all().delete()
