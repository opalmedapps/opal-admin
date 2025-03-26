
import datetime as dt
import json

from django.utils import timezone

import pytest

from opal.caregivers import factories as caregivers_factories
from opal.core.test_utils import CommandTestMixin
from opal.legacy.models import LegacyPatientActivityLog
from opal.patients import factories as patients_factories
from opal.patients import models as patient_models
from opal.usage_statistics import factories as statistics_factory
from opal.usage_statistics.models import DailyUserAppActivity, DailyUserPatientActivity

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestDailyUsageStatisticsUpdate(CommandTestMixin):
    """Test class to group the `update_daily_usage_statistics` command tests."""

    def test_no_app_statistics(self) -> None:
        """Ensure that the command does not fail when there is no app statistics."""
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 0
        assert DailyUserPatientActivity.objects.count() == 0

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
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 1
        assert DailyUserPatientActivity.objects.count() == 0

    def test_existing_statistics_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure that the command's force-delete flag deletes the data in models."""
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregivers_factories.Caregiver(username='marge'),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregivers_factories.Caregiver(username='homer'),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregivers_factories.Caregiver(username='bart'),
        )
        marge_caregiver = caregivers_factories.CaregiverProfile(
            user=caregivers_factories.Caregiver(username='marge'),
            legacy_id=51,
        )
        self_relationship = patients_factories.Relationship(
            type=patients_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patients_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
        )
        caregiver_relationship = patients_factories.Relationship(
            type=patients_factories.RelationshipType(role_type=patient_models.RoleType.CAREGIVER),
            patient=patients_factories.Patient(legacy_id=52, ramq='TEST01161973'),
            caregiver=marge_caregiver,
        )
        mandatry_relationship = patients_factories.Relationship(
            type=patients_factories.RelationshipType(role_type=patient_models.RoleType.MANDATARY),
            patient=patients_factories.Patient(legacy_id=53, ramq='TEST01161974'),
            caregiver=marge_caregiver,
        )
        statistics_factory.DailyUserPatientActivity(user_relationship_to_patient=self_relationship)
        statistics_factory.DailyUserPatientActivity(user_relationship_to_patient=caregiver_relationship)
        statistics_factory.DailyUserPatientActivity(user_relationship_to_patient=mandatry_relationship)
        monkeypatch.setattr('builtins.input', lambda _: 'yes')
        stdout, _stderr = self._call_command('update_daily_usage_statistics', '--force-delete')
        assert stdout == 'Deleting existing usage statistics data\nSuccessfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 0
        assert DailyUserPatientActivity.objects.count() == 0
