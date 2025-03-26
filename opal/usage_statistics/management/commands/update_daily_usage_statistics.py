"""Command for populating the application activity statistics to the statistics models on daily basis."""

import datetime as dt
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.db import models, transaction
from django.utils import timezone

from opal.legacy import models as legacy_models
from opal.patients.models import Patient, Relationship, RelationshipStatus
from opal.usage_statistics import utils as stats_utils
from opal.usage_statistics.models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity
from opal.users.models import User


class Command(BaseCommand):
    """
    Command to update the daily app activity statistics per user and patient.

    The command populates `DailyUserAppActivity`, `DailyUserPatientActivity` and `DailyPatientDataReceived` models.
    """

    help = '{0}\n{1}'.format(  # noqa: A003
        'Populate the daily app activity statistics per user and patient from PatientActivityLog',
        'By default the command calculates the statistics for the complete previous day',
    )

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
            help='Calculate the usage statistics for the current day between midnight and now (default: false)',
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """Populate the daily application activities to the statistics models.

        The statistics are populated to the `DailyUserAppActivity`, `DailyUserPatientActivity`
        and `DailyPatientDataReceived` models.

        By default, the command calculates the usage statistics for the previous complete day (e.g., 00:00:00-23:59:59).

        Args:
            args: input arguments
            options:  additional keyword arguments
        """
        # Convenient CL argument for testing; it does not work in production environment
        if options['force_delete'] and self._delete_stored_statistics() is not True:
            return

        # By default the command extract the statistics for the previous day
        days_delta = 1

        # Optional today parameter for calculating app statistics for the current day between 00:00:00 and 23:59:59
        if options['today']:
            self.stdout.write(self.style.WARNING('Calculating usage statistics for today'))
            days_delta = 0

        # NOTE: timezone.now() returns a datetime in UTC timezone.
        # It must be converted to the local timezone since the dates stored in the legacy DB are not UTC.
        # Set the default query time period for the previous complete day (e.g., between 00:00:00 and 23:59:59)
        start_datetime_period = dt.datetime.combine(
            dt.datetime.now() - dt.timedelta(days=days_delta),
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

        self._populate_user_patient_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        )

        self._populate_patient_received_data(
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
        users = User.objects.values('id', 'username')
        users_dict = {user['username']: user['id'] for user in users}

        activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        )

        DailyUserAppActivity.objects.bulk_create(
            DailyUserAppActivity(
                action_by_user_id=users_dict[activity.pop('username')],
                **activity,
            ) for activity in activities
        )

    def _populate_user_patient_app_activities(
        self,
        start_datetime_period: dt.datetime,
        end_datetime_period: dt.datetime,
    ) -> None:
        """Create daily user-patient application activity statistics records in `DailyUserPatientActivity` model.

        Args:
            start_datetime_period: the beginning of the time period of patients' app activities being extracted
            end_datetime_period: the end of the time period of patients' app activities being extracted
        """
        activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        )

        # Fetch relationships where:
        #   - relationship's end_date is greater or equal activity's date OR is empty (e.g., None)
        #   - OR relationship status is CONFIRMED (e.g., the end_date is less than activity's date and CONFIRMED)
        #
        # Since between the same patient and caregiver might be many different relationships,
        # the query fetches only one record per patient <===> caregiver relationship with the maximum end_date
        relationships = Relationship.objects.select_related(
            'patient',
            'caregiver__user',
        ).filter(
            models.Q(end_date__gte=start_datetime_period.date()) | models.Q(end_date=None)
            | models.Q(status=RelationshipStatus.CONFIRMED),
        ).exclude(
            models.Q(status=RelationshipStatus.PENDING)
            | models.Q(status=RelationshipStatus.DENIED),
        ).values(
            'patient__legacy_id',
            'patient__id',
            'caregiver__user__username',
            'caregiver__user__id',
            'id',
        ).annotate(
            end_date=models.Max('end_date'),
        )

        relationships_dict = stats_utils.RelationshipMapping(relationships)

        patient_activities_list = stats_utils.annotate_patient_activities(
            activities,
            relationships_dict,
        )

        DailyUserPatientActivity.objects.bulk_create(patient_activities_list)

    def _populate_patient_received_data(
        self,
        start_datetime_period: dt.datetime,
        end_datetime_period: dt.datetime,
    ) -> None:
        """Create daily patients' received data statistics records in `DailyPatientDataReceived` model.

        Args:
            start_datetime_period: the beginning of the time period of received data statistics being extracted
            end_datetime_period: the end of the time period of received data statistics being extracted
        """
        received_data = stats_utils.get_aggregated_patient_received_data(
            start_datetime_period=start_datetime_period,
            end_datetime_period=end_datetime_period,
        )
        patients = Patient.objects.values('id', 'legacy_id')
        patients_dict = {patient['legacy_id']: patient['id'] for patient in patients}

        DailyPatientDataReceived.objects.bulk_create(
            DailyPatientDataReceived(
                patient_id=patients_dict[data.pop('patient')],
                **data,
            ) for data in received_data
        )

    def _delete_stored_statistics(self) -> bool:
        """Delete daily application activity statistics data.

        The records are deleted from the `DailyUserAppActivity`, `DailyUserPatientActivity`
        an `DailyPatientDataReceived` models.

        Returns:
            True, if the records were deleted, False otherwise
        """
        if settings.DEBUG is False:
            self.stdout.write(self.style.WARNING(
                'Existing usage statistics data cannot be deleted in production environment',
            ))
            return False

        self.stdout.write(self.style.WARNING('Deleting existing usage statistics data'))
        confirm = input(
            'Are you sure you want to do this?\n'
            + '\n'
            + "Type 'yes' to continue, or 'no' to cancel: ",
        )

        if confirm != 'yes':
            self.stdout.write('Usage statistics update is cancelled')
            return False

        DailyUserAppActivity.objects.all().delete()
        DailyUserPatientActivity.objects.all().delete()
        DailyPatientDataReceived.objects.all().delete()

        return True
