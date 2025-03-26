
import datetime as dt
import json

from django.utils import timezone

import pytest

from opal.caregivers import factories as caregivers_factories
from opal.core.test_utils import CommandTestMixin
from opal.legacy.models import LegacyPatientActivityLog
from opal.usage_statistics.models import DailyUserAppActivity

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestDailyUsageStatisticsUpdate(CommandTestMixin):
    """Test class to group the `update_daily_usage_statistics` command tests."""

    def test_no_app_statistics(self) -> None:
        """Ensure that the command does not fail when there is no app statistics."""
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated statistics data to DailyUserAppActivity model\n'

    def test_populate_previous_day_user_statistics(self) -> None:
        """Ensure that the command successfully populates the previous day app statistics."""
        caregiver = caregivers_factories.CaregiverProfile()
        LegacyPatientActivityLog.objects.bulk_create([
            LegacyPatientActivityLog(
                request='Login',
                parameters='',
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='QuestionnaireNumberUnread',
                parameters=json.dumps({'purpose': 'clinical'}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='QuestionnaireNumberUnread',
                parameters=json.dumps({'purpose': 'research'}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='QuestionnaireNumberUnread',
                parameters=json.dumps({'purpose': 'consent'}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='Feedback',
                parameters='OMITTED',
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='UpdateSecurityQuestionAnswer',
                parameters='OMITTED',
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='AccountChange',
                parameters='OMITTED',
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='AccountChange',
                parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'FR'}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='AccountChange',
                parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='DeviceIdentifier',
                parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='DeviceIdentifier',
                parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='DeviceIdentifier',
                parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
            LegacyPatientActivityLog(
                request='Logout',
                parameters='',
                target_patient_id=None,
                username=caregiver.user.username,
                date_time=timezone.now() - dt.timedelta(days=1),
                app_version='100.100.100',
            ),
        ])
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated statistics data to DailyUserAppActivity model\n'
        assert DailyUserAppActivity.objects.count() == 1
