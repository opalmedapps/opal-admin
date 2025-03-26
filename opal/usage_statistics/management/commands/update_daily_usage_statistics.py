"""Command for updating the `DailyUserAppActivity` model on daily basis.

TODO
- Determine how to capture activity clicked via the Home tab Notifications menu.
These are logged different in PAL than regular Chart activity.
- Ticket to fix the PAL logging of Account language change, bug described in spike doc
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
            self.stdout.write(self.style.WARNING('Deleting existing data'))
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
        for activity in activities:
            user = User.objects.filter(username=activity['username']).first()
            patient_data_owner = Patient.objects.filter(legacy_id=activity['target_patient_id']).first()
            caregiver_profile = CaregiverProfile.objects.filter(user=user).first()

            # TODO: Decide if this final check is worth doing
            # Since the original query returns each unique pairing of patient+user, we have the potential to have
            #     several 'useless' records created here.
            # For example, if Fred Flintstone logged in once, did nothing and logged out
            #     in the query reference time period, then here we would create one row for
            # Fred's user activity with count_login=1, and everything else 0/null.
            #     PLUS another record for each Patient the user fred is associated with
            #     (So one for Fred<-->Pebbles and one for Fred<-->Fred)
            # These extra 2 empty rows will be created even if all of their values are 0/null,
            #     because the Relationship itself is confirmed.
            # That can potentially add a lot of bloat to this table.
            # So one option is to just filter out these 'useless' records from being saved
            conditions = [
                activity['last_login'] is not None,
                activity['count_logins'] > 0,
                activity['count_checkins'] > 0,
                activity['count_documents'] > 0,
                activity['count_educational_materials'] > 0,
                activity['count_feedback'] > 0,
                activity['count_questionnaires_complete'] > 0,
                activity['count_labs'] > 0,
                activity['count_update_security_answers'] > 0,
                activity['count_update_passwords'] > 0,
                activity['count_update_language'] > 0,
                activity['count_device_ios'] > 0,
                activity['count_device_android'] > 0,
                activity['count_device_browser'] > 0,
            ]
            # The other option to solve this problem would be to filter out these 0/null results in the original query
            # using a secondary filter to mimic the MySQL `HAVING` clause, eg
            # .filter(
            #     Q(last_login__isnull=False) |
            #     Q(count_logins__gt=0) |
            #     Q(count_checkins__gt=0) |

            if any(conditions):
                DailyUserAppActivity(
                    action_by_user=user,
                    # Feedback: It makes sense to filter only confirmed relationships... I think?
                    user_relationship_to_patient=Relationship.objects.filter(
                        patient=patient_data_owner,
                        caregiver=caregiver_profile,
                        status=RelationshipStatus.CONFIRMED,
                    ).first(),
                    patient=patient_data_owner,
                    last_login=activity['last_login'],
                    count_logins=activity['count_logins'],
                    count_checkins=activity['count_checkins'],
                    count_documents=activity['count_documents'],
                    count_educational_materials=activity['count_educational_materials'],
                    count_feedback=activity['count_feedback'],
                    count_questionnaires_complete=activity['count_questionnaires_complete'],
                    count_labs=activity['count_labs'],
                    count_update_security_answers=activity['count_update_security_answers'],
                    count_update_passwords=activity['count_update_passwords'],
                    count_update_language=activity['count_update_language'],
                    count_device_ios=activity['count_device_ios'],
                    count_device_android=activity['count_device_android'],
                    count_device_browser=activity['count_device_browser'],
                    date_added=timezone.now().date(),
                ).save()
