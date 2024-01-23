"""Daily command to update the Usage Statistics models."""

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
    """Command to update the daily usage statistics tables."""

    help = 'Populate UserAppActivity from PatientActivityLog'  # noqa: A003

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

    def handle(self, *args, **options):  # noqa: WPS210
        """
        Handle daily calculation of statistics and append to reporting tables.

        Return 'None'.

        Args:
            args: input arguments.
            options:  additional keyword arguments.
        """
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

        # TODO: Remove
        # Optionally use today as the query time period instead for easier testing (00:00:00-23:59:59)
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
                hour=23,
                minute=59,
                second=59,
                microsecond=0,
            )

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
            count_device_browser=Count('DeviceId', filter=Q(Parameters__contains='Browser'), distinct=True),
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
                date_added=current_datetime.date(),
            )
            user_app_activity.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated UserAppActivity'))
