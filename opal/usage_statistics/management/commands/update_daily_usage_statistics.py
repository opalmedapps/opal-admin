"""Daily command to update the Usage Statistics models."""

import datetime as dt

from django.core.management.base import BaseCommand
from django.db.models import Count, F, Max, Q  # noqa: WPS347
from django.utils import timezone

from opal.caregivers.models import CaregiverProfile
from opal.legacy.models import LegacyPatientActivityLog
from opal.patients.models import Patient, Relationship, RelationshipStatus
from opal.usage_statistics.models import UserAppActivity
from opal.users.models import User


class Command(BaseCommand):
    """Command to update the daily usage statistics tables."""

    help = 'Populate UserAppActivity from PatientActivityLog'  # noqa: A003

    def handle(self, *args, **kwargs):  # noqa: WPS210
        """
        Handle daily calculation of statistics and append to reporting tables.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs:  variable keyword input arguments.
        """
        current_datetime = timezone.now()
        start_of_previous_day = current_datetime.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ) - dt.timedelta(days=1)
        end_of_previous_day = start_of_previous_day + dt.timedelta(days=1) - dt.timedelta(microseconds=1)  # noqa: WPS221
        # Aggregating data similar to the SQL query
        activities = LegacyPatientActivityLog.objects.filter(
            DateTime__gte=start_of_previous_day,
            DateTime__lt=end_of_previous_day,
        ).values('TargetPatientId', 'Username').annotate(
            last_login=Max('DateTime'),
            count_logins=Count('ActivitySerNum', filter=F('Request') == 'Login'),  # noqa: WPS204
            # TODO:
            # Verify if this is only counting successful checkins or if failed attempts get lumped together
            count_checkins=Count('ActivitySerNum', filter=F('Request') == 'Checkin'),
            count_documents=Count('ActivitySerNum', filter=F('Request') == 'DocumentContent'),
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
            count_educational_materials=Count('ActivitySerNum', filter=F('Request') == 'Log'),
            count_feedback=Count('ActivitySerNum', filter=F('Request') == 'Feedback'),
            count_questionnaires_complete=Count(
                'ActivitySerNum',
                filter=Q(Request='Checkin') and Q(Parameters__contains='"new_status":"2"'),
            ),
            count_labs=Count(
                'ActivitySerNum',
                filter=Q(Request='PatientTestTypeResults') or Q(Request='PatientTestDateResults'),
            ),
            count_update_security_answers=Count(
                'ActivitySerNum',
                filter=F('Request') == 'UpdateSecurityQuestionAnswer',
            ),
            # Password change PAL shows OMITTED for parameters... is this unique to password updates?
            count_update_passwords=Count(
                'ActivitySerNum',
                filter=Q(Request='AccountChange') and Q(Parameters='OMITTED'),
            ),
            count_update_language=Count(
                'ActivitySerNum',
                filter=Q(Request='AccountChange') and Q(Parameters__contains='"Language"'),
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
        print('Got activities')
        print(activities)
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
