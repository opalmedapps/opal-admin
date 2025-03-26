import datetime as dt
import json
from typing import Optional

from django.utils import timezone

import pytest
from faker import Faker

from opal.caregivers import factories as caregiver_factories
from opal.core.test_utils import CommandTestMixin
from opal.legacy import factories as legacy_factories
from opal.legacy import models as legacy_models
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.usage_statistics import factories as statistics_factory
from opal.usage_statistics.models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestDailyUsageStatisticsUpdate(CommandTestMixin):
    """Test class to group the `update_daily_usage_statistics` command tests."""

    def test_no_app_statistics(self) -> None:
        """Ensure that the command does not fail when there is no app statistics."""
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 0
        assert DailyUserPatientActivity.objects.count() == 0
        assert DailyPatientDataReceived.objects.count() == 0

    def test_existing_statistics_delete_yes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure that the command's force-delete flag deletes the data in models."""
        monkeypatch.setattr('django.conf.settings.DEBUG', {'DEBUG': True})
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(username='marge'),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(username='homer'),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(username='bart'),
        )
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
        )
        caregiver_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.CAREGIVER),
            patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
            caregiver=marge_caregiver,
        )
        mandatry_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.MANDATARY),
            patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
            caregiver=marge_caregiver,
        )
        statistics_factory.DailyUserPatientActivity(user_relationship_to_patient=self_relationship)
        statistics_factory.DailyUserPatientActivity(user_relationship_to_patient=caregiver_relationship)
        statistics_factory.DailyUserPatientActivity(user_relationship_to_patient=mandatry_relationship)
        statistics_factory.DailyPatientDataReceived()
        statistics_factory.DailyPatientDataReceived()
        statistics_factory.DailyPatientDataReceived()
        monkeypatch.setattr('builtins.input', lambda _: 'yes')
        stdout, _stderr = self._call_command('update_daily_usage_statistics', '--force-delete')
        assert stdout == 'Deleting existing usage statistics data\nSuccessfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 0
        assert DailyUserPatientActivity.objects.count() == 0
        assert DailyPatientDataReceived.objects.count() == 0

    def test_existing_statistics_delete_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure that the command's force-delete stops execution if user enters 'no' to the prompt."""
        self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(username='marge'),
        )
        statistics_factory.DailyUserPatientActivity(user_relationship_to_patient=self_relationship)
        statistics_factory.DailyPatientDataReceived()
        monkeypatch.setattr('django.conf.settings.DEBUG', {'DEBUG': True})
        monkeypatch.setattr('builtins.input', lambda _: 'no')
        stdout, _stderr = self._call_command('update_daily_usage_statistics', '--force-delete')
        assert stdout == 'Deleting existing usage statistics data\nUsage statistics update is cancelled\n'
        assert DailyUserAppActivity.objects.count() == 1
        assert DailyUserPatientActivity.objects.count() == 1
        assert DailyPatientDataReceived.objects.count() == 1

    def test_existing_statistics_delete_in_prod_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure that the command's force-delete flag is forbidden in production environment."""
        stdout, _stderr = self._call_command('update_daily_usage_statistics', '--force-delete')
        assert stdout == 'Existing usage statistics data cannot be deleted in production environment\n'

    # tests for populating user app activities

    def test_populate_previous_day_user_statistics(self) -> None:
        """Ensure that the command successfully populates the previous day app statistics per user."""
        caregiver = caregiver_factories.CaregiverProfile()

        self._create_log_record(username=caregiver.user.username)
        self._create_log_record(request='Feedback', parameters='OMITTED', username=caregiver.user.username)
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username=caregiver.user.username,
        )
        self._create_log_record(request='AccountChange', parameters='OMITTED', username=caregiver.user.username)
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'FR'}),
            username=caregiver.user.username,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
            username=caregiver.user.username,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=caregiver.user.username,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=caregiver.user.username,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=caregiver.user.username,
        )
        self._create_log_record(request='Logout', username=caregiver.user.username)
        # current day records should not be populated to the `DailyUserAppActivity`
        self._create_log_record(username=caregiver.user.username, days_delta=0)
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=caregiver.user.username, days_delta=0,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=caregiver.user.username,
            days_delta=0,
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 1
        user_app_activity = DailyUserAppActivity.objects.first()
        assert user_app_activity
        assert user_app_activity.count_logins == 1
        assert user_app_activity.count_feedback == 1
        assert user_app_activity.count_update_security_answers == 1
        assert user_app_activity.count_update_passwords == 1
        assert user_app_activity.count_update_language == 2
        current_day = dt.datetime.now().date()
        previous_day = current_day - dt.timedelta(days=1)
        assert user_app_activity.action_date == previous_day

    def test_populate_current_day_user_statistics(self) -> None:
        """Ensure that the command successfully populates the current day app statistics per user."""
        caregiver = caregiver_factories.CaregiverProfile()
        self._create_log_record(username=caregiver.user.username, days_delta=0)
        self._create_log_record(
            request='Feedback',
            parameters='OMITTED',
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'FR'}),
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(request='Logout', username=caregiver.user.username, days_delta=0)
        # The previous day records should not be populated to the `DailyUserAppActivity`
        self._create_log_record(username=caregiver.user.username)
        self._create_log_record(request='Feedback', parameters='OMITTED', username=caregiver.user.username)
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=caregiver.user.username,
        )
        self._create_log_record(request='AccountChange', parameters='OMITTED', username=caregiver.user.username)
        stdout, _stderr = self._call_command('update_daily_usage_statistics', '--today')
        assert stdout == 'Calculating usage statistics for today\nSuccessfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 1
        user_app_activity = DailyUserAppActivity.objects.first()
        assert user_app_activity
        assert user_app_activity.count_logins == 1
        assert user_app_activity.count_feedback == 1
        assert user_app_activity.count_update_security_answers == 1
        assert user_app_activity.count_update_passwords == 1
        assert user_app_activity.count_update_language == 2
        assert user_app_activity.action_date == dt.datetime.now().date()

    def test_populate_last_login_user_statistics(self) -> None:
        """Ensure that the command correctly populates the last login time per user per day."""
        fake = Faker()
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        start_datetime_period = dt.datetime.combine(
            dt.datetime.now(),
            dt.datetime.min.time(),
            timezone.get_current_timezone(),
        )
        end_datetime_period = dt.datetime.combine(
            start_datetime_period,
            dt.datetime.max.time(),
            timezone.get_current_timezone(),
        )
        marge_two_days_ago_date_time = fake.date_time_between(
            start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
        ) - dt.timedelta(days=2)
        homer_two_days_ago_date_time = fake.date_time_between(
            start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
        ) - dt.timedelta(days=2)
        marge_previous_day_date_time = fake.date_time_between(
            start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
        ) - dt.timedelta(days=1)
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            last_login=marge_two_days_ago_date_time,
            action_date=start_datetime_period.date() - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            last_login=homer_two_days_ago_date_time,
            action_date=start_datetime_period.date() - dt.timedelta(days=2),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=marge_caregiver.user.username, target_patient_id=None, date_time=marge_previous_day_date_time,
        )
        previous_day_min_time = dt.datetime.combine(
            marge_previous_day_date_time, dt.datetime.min.time(), timezone.get_current_timezone(),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=marge_caregiver.user.username,
            target_patient_id=None,
            date_time=fake.date_time_between(
                previous_day_min_time, marge_previous_day_date_time, timezone.get_current_timezone(),
            ),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=marge_caregiver.user.username,
            target_patient_id=None,
            date_time=fake.date_time_between(
                previous_day_min_time, marge_previous_day_date_time, timezone.get_current_timezone(),
            ),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=marge_caregiver.user.username,
            target_patient_id=None,
            date_time=fake.date_time_between(
                start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
            ),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=homer_caregiver.user.username,
            target_patient_id=None,
            date_time=fake.date_time_between(
                start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
            ) - dt.timedelta(days=1),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=homer_caregiver.user.username,
            target_patient_id=None,
            date_time=fake.date_time_between(
                start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
            ) - dt.timedelta(days=1),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=homer_caregiver.user.username,
            target_patient_id=None,
            date_time=fake.date_time_between(
                start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
            ) - dt.timedelta(days=1),
        )
        legacy_factories.LegacyPatientActivityLogFactory(
            username=homer_caregiver.user.username,
            target_patient_id=None,
            date_time=fake.date_time_between(
                start_datetime_period, end_datetime_period, timezone.get_current_timezone(),
            ),
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=marge_two_days_ago_date_time,
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.last_login == marge_two_days_ago_date_time
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=start_datetime_period.date() - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        marge_last_login_previous_day = legacy_models.LegacyPatientActivityLog.objects.filter(
            username=marge_caregiver.user,
            date_time__date=marge_previous_day_app_activity.action_date,
        ).order_by(
            '-date_time',
        ).first()
        assert marge_last_login_previous_day
        assert marge_previous_day_app_activity.last_login == marge_last_login_previous_day.date_time
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=start_datetime_period.date(),
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_login_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates logins count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_logins=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_logins=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(username=marge_caregiver.user.username, days_delta=1)
        self._create_log_record(username=marge_caregiver.user.username, days_delta=1)
        self._create_log_record(username=marge_caregiver.user.username, days_delta=1)
        self._create_log_record(username=marge_caregiver.user.username, days_delta=0)
        self._create_log_record(username=homer_caregiver.user.username, days_delta=1)
        self._create_log_record(username=homer_caregiver.user.username, days_delta=1)
        self._create_log_record(username=homer_caregiver.user.username, days_delta=1)
        self._create_log_record(username=homer_caregiver.user.username, days_delta=0)
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_logins == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_logins == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_feedback_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates feedback count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_feedback=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_feedback=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=marge_caregiver.user.username, days_delta=1,
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=marge_caregiver.user.username, days_delta=1,
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=marge_caregiver.user.username, days_delta=1,
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=marge_caregiver.user.username, days_delta=0,
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=homer_caregiver.user.username, days_delta=1,
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=homer_caregiver.user.username, days_delta=1,
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=homer_caregiver.user.username, days_delta=1,
        )
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=homer_caregiver.user.username, days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_feedback == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_feedback == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_security_answer_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates updated security answers count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_update_security_answers=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_update_security_answers=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='UpdateSecurityQuestionAnswer',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_update_security_answers == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_update_security_answers == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_password_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates updated passwords count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_update_passwords=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_update_passwords=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters='OMITTED',
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_update_passwords == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_update_passwords == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_language_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates language updates count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_update_language=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_update_language=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'FR'}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'FR'}),
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'FR'}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='AccountChange',
            parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'FR'}),
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_update_language == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_update_language == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_android_device_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates android devices count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_device_android=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_device_android=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'Android', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_device_android == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_device_android == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_ios_device_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates iOS devices count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_device_ios=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_device_ios=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'iOS', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        assert DailyUserPatientActivity.objects.count() == 0
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_device_ios == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_device_ios == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    def test_populate_browser_device_user_statistics(self) -> None:
        """Ensure that the command correctly aggregates browser devices count per user per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        date = dt.datetime.now().date()
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            count_device_browser=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserAppActivity(
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            count_device_browser=1,
            action_date=date - dt.timedelta(days=2),
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DeviceIdentifier',
            parameters=json.dumps({'deviceType': 'browser', 'registrationId': ''}),
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 4
        marge_two_days_ago_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_app_activity
        assert marge_two_days_ago_app_activity.count_device_browser == 1
        marge_previous_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_app_activity
        assert marge_previous_day_app_activity.count_device_browser == 3
        marge_current_day_app_activity = DailyUserAppActivity.objects.filter(
            action_by_user=marge_caregiver.user,
            action_date=date,
        ).first()
        assert marge_current_day_app_activity is None

    # tests for populating patient app activities

    def test_populate_previous_day_patient_statistics(self) -> None:
        """Ensure that the command successfully populates the previous day app statistics per patient."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )

        patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        self._create_log_record(username=marge_caregiver.user.username)
        self._create_log_record(request='Feedback', parameters='OMITTED', username=marge_caregiver.user.username)

        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters=json.dumps(['1']),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters=json.dumps(['2']),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '1', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '2', 'new_status': '1', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='PatientTestTypeResults',
            parameters=json.dumps({'testTypeSerNum': '1'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 05 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )

        # current day records should not be populated to the `DailyUserPatientActivity`
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters=json.dumps(['3']),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '3', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 1
        assert DailyUserPatientActivity.objects.count() == 1
        patient_activity = DailyUserPatientActivity.objects.first()
        assert patient_activity
        assert patient_activity.count_checkins == 1
        assert patient_activity.count_documents == 2
        assert patient_activity.count_educational_materials == 1
        assert patient_activity.count_questionnaires_complete == 1
        assert patient_activity.count_labs == 2

    def test_populate_current_day_patient_statistics(self) -> None:
        """Ensure that the command successfully populates the current day app statistics per patient."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )

        patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        self._create_log_record(username=marge_caregiver.user.username, days_delta=0)
        self._create_log_record(
            request='Feedback', parameters='OMITTED', username=marge_caregiver.user.username, days_delta=0,
        )

        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters=json.dumps(['1']),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters=json.dumps(['2']),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '1', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '2', 'new_status': '1', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='PatientTestTypeResults',
            parameters=json.dumps({'testTypeSerNum': '1'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 05 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )

        # The previous day records should not be populated to the `DailyUserAppActivity`
        self._create_log_record(username=marge_caregiver.user.username)
        self._create_log_record(request='Feedback', parameters='OMITTED', username=marge_caregiver.user.username)

        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters=json.dumps(['3']),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '3', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics', '--today')
        assert stdout == 'Calculating usage statistics for today\nSuccessfully populated daily statistics data\n'
        assert DailyUserAppActivity.objects.count() == 1
        assert DailyUserPatientActivity.objects.count() == 1
        patient_activity = DailyUserPatientActivity.objects.first()
        assert patient_activity
        assert patient_activity.count_checkins == 1
        assert patient_activity.count_documents == 2
        assert patient_activity.count_educational_materials == 1
        assert patient_activity.count_questionnaires_complete == 1
        assert patient_activity.count_labs == 2

    def test_populate_checkin_statistics(self) -> None:
        """Ensure that the command correctly aggregates checkins count per patient per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        marge_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        homer_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
            caregiver=homer_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        date = dt.datetime.now().date()
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            patient=marge_self_relationship.patient,
            count_checkins=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=homer_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            patient=homer_self_relationship.patient,
            count_checkins=1,
            action_date=date - dt.timedelta(days=2),
        )

        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Checkin',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserPatientActivity.objects.count() == 4
        marge_two_days_ago_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_patient_activity
        assert marge_two_days_ago_patient_activity.count_checkins == 1
        marge_previous_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_patient_activity
        assert marge_previous_day_patient_activity.count_checkins == 3
        marge_current_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date,
        ).first()
        assert marge_current_day_patient_activity is None

    def test_populate_document_statistics(self) -> None:
        """Ensure that the command correctly aggregates documents count per patient per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        marge_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        homer_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
            caregiver=homer_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        date = dt.datetime.now().date()
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            patient=marge_self_relationship.patient,
            count_documents=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=homer_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            patient=homer_self_relationship.patient,
            count_documents=1,
            action_date=date - dt.timedelta(days=2),
        )

        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='DocumentContent',
            parameters='OMITTED',
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserPatientActivity.objects.count() == 4
        marge_two_days_ago_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_patient_activity
        assert marge_two_days_ago_patient_activity.count_documents == 1
        marge_previous_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_patient_activity
        assert marge_previous_day_patient_activity.count_documents == 3
        marge_current_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date,
        ).first()
        assert marge_current_day_patient_activity is None

    def test_populate_educational_material_statistics(self) -> None:
        """Ensure that the command correctly aggregates educational materials count per patient per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        marge_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        homer_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
            caregiver=homer_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        date = dt.datetime.now().date()
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            patient=marge_self_relationship.patient,
            count_educational_materials=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=homer_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            patient=homer_self_relationship.patient,
            count_educational_materials=1,
            action_date=date - dt.timedelta(days=2),
        )

        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '2'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '3'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '4'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '5'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '6'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '7'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='Log',
            parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '8'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserPatientActivity.objects.count() == 4
        marge_two_days_ago_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_patient_activity
        assert marge_two_days_ago_patient_activity.count_educational_materials == 1
        marge_previous_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_patient_activity
        assert marge_previous_day_patient_activity.count_educational_materials == 3
        marge_current_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date,
        ).first()
        assert marge_current_day_patient_activity is None

    def test_populate_questionnaire_statistics(self) -> None:
        """Ensure that the command correctly aggregates questionnaires count per patient per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        marge_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        homer_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
            caregiver=homer_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        date = dt.datetime.now().date()
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            patient=marge_self_relationship.patient,
            count_questionnaires_complete=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=homer_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            patient=homer_self_relationship.patient,
            count_questionnaires_complete=1,
            action_date=date - dt.timedelta(days=2),
        )

        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '1', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '2', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '3', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '4', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '5', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '6', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '7', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='QuestionnaireUpdateStatus',
            parameters=json.dumps({
                'answerQuestionnaire_id': '8', 'new_status': '2', 'user_display_name': 'Marge Simpson',
            }).replace(' ', ''),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserPatientActivity.objects.count() == 4
        marge_two_days_ago_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_patient_activity
        assert marge_two_days_ago_patient_activity.count_questionnaires_complete == 1
        marge_previous_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_patient_activity
        assert marge_previous_day_patient_activity.count_questionnaires_complete == 3
        marge_current_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date,
        ).first()
        assert marge_current_day_patient_activity is None

    def test_populate_lab_statistics(self) -> None:
        """Ensure that the command correctly aggregates lab results count per patient per day."""
        marge_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge'),
            legacy_id=1,
        )
        marge_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
            caregiver=marge_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        homer_caregiver = caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='homer'),
            legacy_id=2,
        )
        homer_self_relationship = patient_factories.Relationship(
            type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
            patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
            caregiver=homer_caregiver,
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        date = dt.datetime.now().date()
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=marge_caregiver.user.username,
            ),
            patient=marge_self_relationship.patient,
            count_labs=1,
            action_date=date - dt.timedelta(days=2),
        )
        statistics_factory.DailyUserPatientActivity(
            user_relationship_to_patient=homer_self_relationship,
            action_by_user=caregiver_factories.Caregiver(
                username=homer_caregiver.user.username,
            ),
            patient=homer_self_relationship.patient,
            count_labs=1,
            action_date=date - dt.timedelta(days=2),
        )

        self._create_log_record(
            request='PatientTestTypeResults',
            parameters=json.dumps({'testTypeSerNum': '1'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 04 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 04 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 05 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=51,
            username=marge_caregiver.user.username,
            days_delta=0,
        )
        self._create_log_record(
            request='PatientTestTypeResults',
            parameters=json.dumps({'testTypeSerNum': '2'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 04 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 04 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=1,
        )
        self._create_log_record(
            request='PatientTestDateResults',
            parameters=json.dumps({'date': 'Fri May 05 2023 10:00:00 GMT-0400 (Eastern Daylight Time)'}),
            target_patient_id=52,
            username=homer_caregiver.user.username,
            days_delta=0,
        )
        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyUserPatientActivity.objects.count() == 4
        marge_two_days_ago_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=2),
        ).first()
        assert marge_two_days_ago_patient_activity
        assert marge_two_days_ago_patient_activity.count_labs == 1
        marge_previous_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date - dt.timedelta(days=1),
        ).first()
        assert marge_previous_day_patient_activity
        assert marge_previous_day_patient_activity.count_labs == 3
        marge_current_day_patient_activity = DailyUserPatientActivity.objects.filter(
            user_relationship_to_patient=marge_self_relationship,
            action_by_user=marge_caregiver.user,
            patient=marge_self_relationship.patient,
            action_date=date,
        ).first()
        assert marge_current_day_patient_activity is None

    # tests for populating patient received data statistics

    def test_populate_previous_day_received_data(self) -> None:
        """Ensure that the command successfully populates the previous day received data statistics per patient."""
        marge = legacy_factories.LegacyPatientFactory(patientsernum=51, ramq='SIMM18510191')
        homer = legacy_factories.LegacyPatientFactory(patientsernum=52, ramq='SIMM18510192')
        legacy_factories.LegacyPatientControlFactory(patient=marge)
        legacy_factories.LegacyPatientControlFactory(patient=homer)

        django_marge_patient = patient_factories.Patient(legacy_id=marge.patientsernum, ramq='SIMM18510191')
        django_homer_patient = patient_factories.Patient(legacy_id=homer.patientsernum, ramq='SIMM18510192')

        previous_day = timezone.make_aware(
            dt.datetime.now() - dt.timedelta(days=1),
        )
        current_day = timezone.make_aware(dt.datetime.now())

        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=timezone.make_aware(dt.datetime.now() - dt.timedelta(days=7)),
            scheduledstarttime=previous_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=timezone.make_aware(dt.datetime.now() - dt.timedelta(days=7)),
            scheduledstarttime=previous_day,
        )

        next_appointment = timezone.make_aware(
            dt.datetime.now() + dt.timedelta(days=3),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=previous_day,
            scheduledstarttime=next_appointment,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=previous_day,
            scheduledstarttime=next_appointment,
        )

        legacy_factories.LegacyDocumentFactory(
            documentsernum=1,
            patientsernum=marge,
            dateadded=previous_day,
        )
        legacy_factories.LegacyDocumentFactory(
            documentsernum=2,
            patientsernum=homer,
            dateadded=previous_day,
        )

        legacy_factories.LegacyEducationalMaterialFactory(
            patientsernum=marge,
            date_added=previous_day,
        )
        legacy_factories.LegacyEducationalMaterialFactory(
            patientsernum=homer,
            date_added=previous_day,
        )

        legacy_factories.LegacyQuestionnaireFactory(
            patientsernum=marge,
            date_added=previous_day,
        )
        legacy_factories.LegacyQuestionnaireFactory(
            patientsernum=homer,
            date_added=previous_day,
        )

        legacy_factories.LegacyPatientTestResultFactory(
            patient_ser_num=marge,
            date_added=previous_day,
        )
        legacy_factories.LegacyPatientTestResultFactory(
            patient_ser_num=homer,
            date_added=previous_day,
        )

        # current day records should not be included to the final queryset
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_day,
            scheduledstarttime=timezone.make_aware(
                dt.datetime.now() + dt.timedelta(days=7),
            ),
        )
        legacy_factories.LegacyDocumentFactory(
            documentsernum=3,
            patientsernum=marge,
            dateadded=current_day,
        )
        legacy_factories.LegacyEducationalMaterialFactory(
            patientsernum=homer,
            date_added=current_day,
        )
        legacy_factories.LegacyQuestionnaireFactory(
            patientsernum=marge,
            date_added=current_day,
        )
        legacy_factories.LegacyPatientTestResultFactory(
            patient_ser_num=homer,
            date_added=current_day,
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyPatientDataReceived.objects.count() == 2
        marge_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_marge_patient,
        ).first()
        assert marge_received_data
        assert marge_received_data.next_appointment == next_appointment
        assert marge_received_data.last_appointment_received == previous_day
        assert marge_received_data.appointments_received == 1
        assert marge_received_data.last_document_received == previous_day
        assert marge_received_data.documents_received == 1
        assert marge_received_data.last_educational_material_received == previous_day
        assert marge_received_data.educational_materials_received == 1
        assert marge_received_data.last_questionnaire_received == previous_day
        assert marge_received_data.questionnaires_received == 1
        assert marge_received_data.last_lab_received == previous_day
        assert marge_received_data.labs_received == 1

        homer_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_homer_patient,
        ).first()
        assert homer_received_data
        assert homer_received_data.next_appointment == next_appointment
        assert homer_received_data.last_appointment_received == previous_day
        assert homer_received_data.appointments_received == 1
        assert homer_received_data.last_document_received == previous_day
        assert homer_received_data.documents_received == 1
        assert homer_received_data.last_educational_material_received == previous_day
        assert homer_received_data.educational_materials_received == 1
        assert homer_received_data.last_questionnaire_received == previous_day
        assert homer_received_data.questionnaires_received == 1
        assert homer_received_data.last_lab_received == previous_day
        assert homer_received_data.labs_received == 1

    def test_populate_current_day_received_data(self) -> None:
        """Ensure that the command successfully populates the current day received data statistics per patient."""
        marge = legacy_factories.LegacyPatientFactory(patientsernum=51, ramq='SIMM18510191')
        homer = legacy_factories.LegacyPatientFactory(patientsernum=52, ramq='SIMM18510192')
        legacy_factories.LegacyPatientControlFactory(patient=marge)
        legacy_factories.LegacyPatientControlFactory(patient=homer)

        django_marge_patient = patient_factories.Patient(legacy_id=marge.patientsernum, ramq='SIMM18510191')
        django_homer_patient = patient_factories.Patient(legacy_id=homer.patientsernum, ramq='SIMM18510192')

        previous_day = timezone.make_aware(
            dt.datetime.now() - dt.timedelta(days=1),
        )
        current_day = timezone.make_aware(dt.datetime.now())

        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=timezone.make_aware(dt.datetime.now() - dt.timedelta(days=7)),
            scheduledstarttime=current_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=timezone.make_aware(dt.datetime.now() - dt.timedelta(days=7)),
            scheduledstarttime=current_day,
        )

        next_appointment = timezone.make_aware(
            dt.datetime.now() + dt.timedelta(days=3),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=current_day,
            scheduledstarttime=next_appointment,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_day,
            scheduledstarttime=next_appointment,
        )

        legacy_factories.LegacyDocumentFactory(
            documentsernum=1,
            patientsernum=marge,
            dateadded=current_day,
        )
        legacy_factories.LegacyDocumentFactory(
            documentsernum=2,
            patientsernum=homer,
            dateadded=current_day,
        )

        legacy_factories.LegacyEducationalMaterialFactory(
            patientsernum=marge,
            date_added=current_day,
        )
        legacy_factories.LegacyEducationalMaterialFactory(
            patientsernum=homer,
            date_added=current_day,
        )

        legacy_factories.LegacyQuestionnaireFactory(
            patientsernum=marge,
            date_added=current_day,
        )
        legacy_factories.LegacyQuestionnaireFactory(
            patientsernum=homer,
            date_added=current_day,
        )

        legacy_factories.LegacyPatientTestResultFactory(
            patient_ser_num=marge,
            date_added=current_day,
        )
        legacy_factories.LegacyPatientTestResultFactory(
            patient_ser_num=homer,
            date_added=current_day,
        )

        # previous day records should not be included to the final queryset
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=previous_day,
            scheduledstarttime=timezone.make_aware(
                dt.datetime.now() + dt.timedelta(days=7),
            ),
        )
        legacy_factories.LegacyDocumentFactory(
            documentsernum=3,
            patientsernum=marge,
            dateadded=previous_day,
        )
        legacy_factories.LegacyEducationalMaterialFactory(
            patientsernum=homer,
            date_added=previous_day,
        )
        legacy_factories.LegacyQuestionnaireFactory(
            patientsernum=marge,
            date_added=previous_day,
        )
        legacy_factories.LegacyPatientTestResultFactory(
            patient_ser_num=homer,
            date_added=previous_day,
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics', '--today')
        assert stdout == 'Calculating usage statistics for today\nSuccessfully populated daily statistics data\n'
        assert DailyPatientDataReceived.objects.count() == 2
        marge_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_marge_patient,
        ).first()
        assert marge_received_data
        assert marge_received_data.next_appointment == next_appointment
        assert marge_received_data.last_appointment_received == current_day
        assert marge_received_data.appointments_received == 1
        assert marge_received_data.last_document_received == current_day
        assert marge_received_data.documents_received == 1
        assert marge_received_data.last_educational_material_received == current_day
        assert marge_received_data.educational_materials_received == 1
        assert marge_received_data.last_questionnaire_received == current_day
        assert marge_received_data.questionnaires_received == 1
        assert marge_received_data.last_lab_received == current_day
        assert marge_received_data.labs_received == 1

        homer_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_homer_patient,
        ).first()
        assert homer_received_data
        assert homer_received_data.next_appointment == next_appointment
        assert homer_received_data.last_appointment_received == current_day
        assert homer_received_data.appointments_received == 1
        assert homer_received_data.last_document_received == current_day
        assert homer_received_data.documents_received == 1
        assert homer_received_data.last_educational_material_received == current_day
        assert homer_received_data.educational_materials_received == 1
        assert homer_received_data.last_questionnaire_received == current_day
        assert homer_received_data.questionnaires_received == 1
        assert homer_received_data.last_lab_received == current_day
        assert homer_received_data.labs_received == 1

    def test_populate_last_appointment_received(self) -> None:
        """Ensure that the command correctly fetches the last appointment received per patient."""
        marge = legacy_factories.LegacyPatientFactory(patientsernum=51, ramq='SIMM18510191')
        homer = legacy_factories.LegacyPatientFactory(patientsernum=52, ramq='SIMM18510192')
        bart = legacy_factories.LegacyPatientFactory(patientsernum=53, ramq='SIMM18510193')
        legacy_factories.LegacyPatientControlFactory(patient=marge)
        legacy_factories.LegacyPatientControlFactory(patient=homer)
        legacy_factories.LegacyPatientControlFactory(patient=bart)

        django_marge_patient = patient_factories.Patient(legacy_id=marge.patientsernum, ramq='SIMM18510191')
        django_homer_patient = patient_factories.Patient(legacy_id=homer.patientsernum, ramq='SIMM18510192')
        django_bart_patient = patient_factories.Patient(legacy_id=bart.patientsernum, ramq='SIMM18510193')

        current_datetime = timezone.make_aware(dt.datetime.now())
        homer_last_appointment = current_datetime - dt.timedelta(days=3)
        marge_last_appointment = current_datetime - dt.timedelta(days=3)
        bart_last_appointment = current_datetime - dt.timedelta(days=1)

        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=current_datetime - dt.timedelta(days=14),
            scheduledstarttime=current_datetime - dt.timedelta(days=7),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=current_datetime - dt.timedelta(days=7),
            scheduledstarttime=marge_last_appointment,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_datetime - dt.timedelta(days=21),
            scheduledstarttime=current_datetime - dt.timedelta(days=10),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_datetime - dt.timedelta(days=10),
            scheduledstarttime=homer_last_appointment,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=bart,
            date_added=current_datetime - dt.timedelta(days=10),
            scheduledstarttime=bart_last_appointment,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=bart,
            date_added=current_datetime - dt.timedelta(days=1),
            scheduledstarttime=timezone.now(),
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyPatientDataReceived.objects.count() == 3
        marge_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_marge_patient,
        ).first()
        assert marge_received_data
        assert marge_received_data.last_appointment_received == marge_last_appointment

        homer_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_homer_patient,
        ).first()
        assert homer_received_data
        assert homer_received_data.last_appointment_received == homer_last_appointment

        bart_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_bart_patient,
        ).first()
        assert bart_received_data
        assert bart_received_data.last_appointment_received == bart_last_appointment

    def test_populate_next_appointment_received(self) -> None:
        """Ensure that the command correctly fetches the next appointment statistics per patient."""
        marge = legacy_factories.LegacyPatientFactory(patientsernum=51, ramq='SIMM18510191')
        homer = legacy_factories.LegacyPatientFactory(patientsernum=52, ramq='SIMM18510192')
        bart = legacy_factories.LegacyPatientFactory(patientsernum=53, ramq='SIMM18510193')
        legacy_factories.LegacyPatientControlFactory(patient=marge)
        legacy_factories.LegacyPatientControlFactory(patient=homer)
        legacy_factories.LegacyPatientControlFactory(patient=bart)

        django_marge_patient = patient_factories.Patient(legacy_id=marge.patientsernum, ramq='SIMM18510191')
        django_homer_patient = patient_factories.Patient(legacy_id=homer.patientsernum, ramq='SIMM18510192')
        django_bart_patient = patient_factories.Patient(legacy_id=bart.patientsernum, ramq='SIMM18510193')

        current_datetime = timezone.make_aware(dt.datetime.now())
        marge_next_appointment = current_datetime + dt.timedelta(days=1)
        homer_next_appointment = current_datetime + dt.timedelta(days=5)
        bart_next_appointment = current_datetime + dt.timedelta(days=10)

        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=current_datetime - dt.timedelta(days=14),
            scheduledstarttime=current_datetime - dt.timedelta(days=1),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=current_datetime - dt.timedelta(days=7),
            scheduledstarttime=current_datetime + dt.timedelta(days=10),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=current_datetime - dt.timedelta(days=5),
            scheduledstarttime=marge_next_appointment,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_datetime - dt.timedelta(days=21),
            scheduledstarttime=current_datetime - dt.timedelta(days=10),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_datetime - dt.timedelta(days=10),
            scheduledstarttime=current_datetime + dt.timedelta(days=1),
            status='Cancelled',
            state='Closed',
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_datetime - dt.timedelta(days=10),
            scheduledstarttime=homer_next_appointment,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=bart,
            date_added=current_datetime - dt.timedelta(days=5),
            scheduledstarttime=current_datetime + dt.timedelta(days=15),
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=bart,
            date_added=current_datetime - dt.timedelta(days=1),
            scheduledstarttime=bart_next_appointment,
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyPatientDataReceived.objects.count() == 3
        marge_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_marge_patient,
        ).first()
        assert marge_received_data
        assert marge_received_data.next_appointment == marge_next_appointment

        homer_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_homer_patient,
        ).first()
        assert homer_received_data
        assert homer_received_data.next_appointment == homer_next_appointment

        bart_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_bart_patient,
        ).first()
        assert bart_received_data
        assert bart_received_data.next_appointment == bart_next_appointment

    def test_populate_appointments_received_count(self) -> None:
        """Ensure that the command correctly aggregates the appointments received count per patient."""
        marge = legacy_factories.LegacyPatientFactory(patientsernum=51, ramq='SIMM18510191')
        homer = legacy_factories.LegacyPatientFactory(patientsernum=52, ramq='SIMM18510192')
        bart = legacy_factories.LegacyPatientFactory(patientsernum=53, ramq='SIMM18510193')
        legacy_factories.LegacyPatientControlFactory(patient=marge)
        legacy_factories.LegacyPatientControlFactory(patient=homer)
        legacy_factories.LegacyPatientControlFactory(patient=bart)

        django_marge_patient = patient_factories.Patient(legacy_id=marge.patientsernum, ramq='SIMM18510191')
        django_homer_patient = patient_factories.Patient(legacy_id=homer.patientsernum, ramq='SIMM18510192')
        django_bart_patient = patient_factories.Patient(legacy_id=bart.patientsernum, ramq='SIMM18510193')

        current_day = timezone.make_aware(dt.datetime.now())
        previous_day = current_day - dt.timedelta(days=1)

        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=previous_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=previous_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=marge,
            date_added=current_day + dt.timedelta(days=1),
        )

        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=previous_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=previous_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=homer,
            date_added=current_day + dt.timedelta(days=2),
        )

        legacy_factories.LegacyAppointmentFactory(
            patientsernum=bart,
            date_added=previous_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=bart,
            date_added=previous_day,
        )
        legacy_factories.LegacyAppointmentFactory(
            patientsernum=bart,
            date_added=current_day,
        )

        stdout, _stderr = self._call_command('update_daily_usage_statistics')
        assert stdout == 'Successfully populated daily statistics data\n'
        assert DailyPatientDataReceived.objects.count() == 3
        marge_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_marge_patient,
        ).first()
        assert marge_received_data
        assert marge_received_data.appointments_received == 2

        homer_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_homer_patient,
        ).first()
        assert homer_received_data
        assert homer_received_data.appointments_received == 2

        bart_received_data = DailyPatientDataReceived.objects.filter(
            patient_id=django_bart_patient,
        ).first()
        assert bart_received_data
        assert bart_received_data.appointments_received == 2

    def _create_log_record(
        self,
        request: str = 'Login',
        parameters: str = '',
        target_patient_id: Optional[int] = None,
        username: str = 'username',
        app_version: str = '100.100.100',
        days_delta: int = 1,
    ) -> legacy_factories.LegacyPatientActivityLogFactory:
        data = {
            'request': request,
            'parameters': parameters,
            'target_patient_id': target_patient_id,
            'username': username,
            'date_time': timezone.localtime(timezone.now()) - dt.timedelta(days=days_delta),
            'app_version': app_version,
        }
        return legacy_factories.LegacyPatientActivityLogFactory(**data)
