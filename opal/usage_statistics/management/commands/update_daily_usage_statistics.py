"""Daily command to update the Usage Statistics models."""

import datetime as dt

from django.core.management.base import BaseCommand
from django.db.models import Count, F, Max, Value
from django.db.models.functions import TruncDate

from opal.legacy.models import LegacyPatientActivityLog
from opal.usage_statistics.models import UserAppActivity
from opal.patients.models import Patient, Relationship, RelationshipStatus
from opal.users.models import User
from opal.caregivers.models import CaregiverProfile

class Command(BaseCommand):
    """Command to update the daily usage statistics tables."""

    help = 'Populate UserAppActivity from PatientActivityLog'  # noqa: A003

    def handle(self, *args, **kwargs):
        """
        Handle daily calculation of statistics and append to reporting tables.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs:  variable keyword input arguments.
        """
        # Aggregating data similar to the SQL query
        activities = LegacyPatientActivityLog.objects.filter(
            DateTime__gte=TruncDate(Value('now')) - dt.timedelta(days=1),
            DateTime__lt=TruncDate(Value('now')),
        ).values('TargetPatientId', 'Username').annotate(
            last_login=Max('DateTime'),
            count_logins=Count('ActivitySerNum', filter=F('Request') == 'Login'),
            count_checkins=Count('ActivitySerNum', filter=F('Request') == 'Checkin'),
            count_documents=Count('ActivitySerNum', filter=F('Request') == 'DocumentContent'),
            # educ is tricky... the different educ types get logged different in PAL table
            # Package --> Request==Log, Parameters={"Activity":"EducationalMaterialSerNum","ActivityDetails":"6"}
            #         + for each content Request==Log, Parameters={"Activity":"EducationalMaterialControlSerNum","ActivityDetails":"649"}
            #         + etc
            # Factsheet --> Request=Log, Parameters={"Activity":"EducationalMaterialSerNum","ActivityDetails":"11"}
            # Booklet --> Log + {"Activity":"EducationalMaterialSerNum","ActivityDetails":"4"}
            #         + for each chapter Request=Read, Parameters={"Field":"EducationalMaterial","Id":"4"}
            count_educational_materials=Count('ActivitySerNum', filter=F('Request') == 'EducationalMaterial'),
            count_feedback=Count('ActivitySerNum', filter=F('Request') == 'Feedback'),
            count_questionnaires=Count('ActivitySerNum', filter=F('Request') == 'Checkin'),
            count_update_security_answers=Count('ActivitySerNum', filter=F('Request') == 'UpdateSecurityQuestionAnswer'),
            count_update_passwords=Count('ActivitySerNum', filter=F('Request') == 'SetNewPassword'),
            count_labs=Count('ActivitySerNum', filter=F('Request') == 'PatientTestDateResults'),
            # ... other aggregations as per your SQL query
            date_added=TruncDate(Value('now')),
        )

        for activity in activities:
            user = User.objects.filter(username=activity['Username']).first()
            patient_data_owner = Patient.objects.filter(legacy_id=activity['TargetPatientId']).first()
            caregiver_profile = CaregiverProfile.objects.filter(user=user)
            user_app_activity = UserAppActivity(
                action_by_user=user,
                # Feedback: It makes sense to filter only confirmed relationships... I think?
                user_relationship_to_patient=Relationship.objects.filter(
                    patient=patient_data_owner,
                    caregiver=caregiver_profile,
                    status=RelationshipStatus.CONFIRMED,
                ),
                patient=patient_data_owner,
                last_login=activity['last_login'],
                count_logins=activity['count_logins'],
                count_checkins=activity['count_checkins'],
                # ... map other fields accordingly
                date_added=activity['date_added'],
            )
            user_app_activity.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated UserAppActivity'))
