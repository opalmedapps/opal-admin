"""Daily command to update the Usage Statistics models.

TODO
- Determine how to capture activity clicked via the Home tab Notifications menu.
These are logged different in PAL than regular Chart activity.
- Ticket to fix the PAL logging of Account language change, bug described in spike doc
-
"""

import datetime as dt

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Count, Max, Q  # noqa: WPS347
from django.utils import timezone

from opal.caregivers.models import CaregiverProfile
from opal.legacy.models import LegacyPatientActivityLog
from opal.patients.models import Patient, Relationship, RelationshipStatus
from opal.usage_statistics.models import UserAppActivity
from opal.users.models import User


class Command(BaseCommand):
    """Command to update the daily usage statistics and reporting tables."""

    help = 'Populate Usage statistics and reporting from PatientActivityLog'  # noqa: A003

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
            help='Calculate usage for today instead of the default yesterday',
        )

    def handle(self, *args, **options):
        """
        Handle daily calculation of statistics and append to reporting tables.

        Return 'None'.

        Args:
            args: input arguments.
            options:  additional keyword arguments.
        """
        # TODO: Remove, convenience CL arg for testing
        force_delete: bool = options['force_delete']
        if force_delete:
            self.stdout.write(self.style.WARNING('Deleting existing UserAppActivity data'))
            UserAppActivity.objects.all().delete()

        # Set default query time period for all of yesterday
        current_datetime = timezone.now()
        time_period_start = current_datetime.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ) - dt.timedelta(days=1)
        time_period_end = time_period_start + dt.timedelta(days=1) - dt.timedelta(microseconds=1)  # noqa: WPS221

        # TODO: Remove?
        # Optionally use today as the query time period instead of yesterday for easier testing (00:00:00-23:59:59)
        today: bool = options['today']
        if today:
            self.stdout.write(self.style.WARNING('Calculating statistics for today'))
            time_period_start = current_datetime.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            time_period_end = current_datetime.replace(
                hour=23,  # noqa: WPS432
                minute=59,  # noqa: WPS432
                second=59,  # noqa: WPS432
                microsecond=0,
            )

        self._update_user_app_activity(time_period_start=time_period_start, time_period_end=time_period_end)

    def _update_user_app_activity(self, time_period_start, time_period_end) -> None:  # noqa: WPS210
        """Query from PatientActivityLog to generate daily user/patient app activity.

        Args:
            time_period_start: Datetime for the beginning of the query time period
            time_period_end: Datetime for the end of the query time period
        """
        # Aggregating data similar to the SQL query
        activities = LegacyPatientActivityLog.objects.filter(
            DateTime__gte=time_period_start,
            DateTime__lt=time_period_end,
        ).values('TargetPatientId', 'Username').annotate(
            last_login=Max('DateTime', filter=Q(Request='Login')),
            count_logins=Count('ActivitySerNum', filter=Q(Request='Login')),
            # TODO:
            # Verify if this is only counting successful checkins or if failed attempts get lumped together
            count_checkins=Count('ActivitySerNum', filter=Q(Request='Checkin')),
            count_documents=Count('ActivitySerNum', filter=Q(Request='DocumentContent')),
            # educ is tricky... the different educ types get logged different in PAL table
            # Package --> Request==Log, Parameters={"Activity":"EducationalMaterialSerNum","ActivityDetails":"6"}
            #  + for each content Request==Log,
            #       and Parameters={"Activity":"EducationalMaterialControlSerNum","ActivityDetails":"649"}
            #         + etc
            # Factsheet --> Request=Log, Parameters={"Activity":"EducationalMaterialSerNum","ActivityDetails":"11"}
            # Booklet --> Log + {"Activity":"EducationalMaterialSerNum","ActivityDetails":"4"}
            #         + for each chapter Request=Read, Parameters={"Field":"EducationalMaterial","Id":"4"}
            # Might have to use PatientActionLog to properly determine educaitonal material count?
            # Could consider counting each type separately here then aggregating below in the model creation?
            count_educational_materials=Count(
                'ActivitySerNum',
                filter=Q(Request='Log', Parameters__contains='EducationalMaterialSerNum'),
            ),
            count_feedback=Count('ActivitySerNum', filter=Q(Request='Feedback')),
            count_questionnaires_complete=Count(
                'ActivitySerNum',
                filter=Q(Request='QuestionnaireUpdateStatus', Parameters__contains='"new_status":"2"'),
            ),
            count_labs=Count(
                'ActivitySerNum',
                filter=Q(Request='PatientTestTypeResults') | Q(Request='PatientTestDateResults'),
            ),
            count_update_security_answers=Count(
                'ActivitySerNum',
                filter=Q(Request='UpdateSecurityQuestionAnswer'),
            ),
            count_update_passwords=Count(
                'ActivitySerNum',
                filter=Q(Request='AccountChange', Parameters='OMITTED'),
            ),
            count_update_language=Count(
                'ActivitySerNum',
                filter=Q(Request='AccountChange', Parameters__contains='"Language"'),
            ),
            count_device_ios=Count('DeviceId', filter=Q(Parameters__contains='iOS'), distinct=True),
            count_device_android=Count('DeviceId', filter=Q(Parameters__contains='Android'), distinct=True),
            count_device_browser=Count('DeviceId', filter=Q(Parameters__contains='browser'), distinct=True),
        )
        # NOTE: It seems like an activity triggered from the Notifications page is recorded differently from when
        #       the activity is initialized in the chart.
        #       If marge clicks on a TxTeamMessage notification from her Home page,
        #       the PAL shows Request==GetOneItem, Parameters=={"category":"TxTeamMessages","serNum":"3"}.
        #       Whereas if marge clicks a TxTeamMessage from her chart page,
        #       PAL shows Request=Read, Parameters={"Field":"TxTeamMessages","Id":"1"}
        #       ... ugh

        print('DEBUG SQL Query:', str(activities.query))
        for activity in activities:
            user = User.objects.filter(username=activity['Username']).first()
            patient_data_owner = Patient.objects.filter(legacy_id=activity['TargetPatientId']).first()
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
                user_app_activity = UserAppActivity(
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
                )
                user_app_activity.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated UserAppActivity'))

    def _update_patient_data_received(self, time_period_start, time_period_end) -> None:  # noqa: WPS210
        """Query from legacy tables to generate daily user/patient app activity.

        Args:
            time_period_start: Datetime for the beginning of the query time period
            time_period_end: Datetime for the end of the query time period
        """
