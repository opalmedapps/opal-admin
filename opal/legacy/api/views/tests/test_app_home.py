import datetime as dt
from datetime import datetime

from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from opal.legacy import factories, models
from opal.legacy.api.serializers import LegacyAppointmentSerializer
from opal.legacy.api.views.app_home import AppHomeView
from opal.patients import factories as patient_factories
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestHomeAppView:
    """Class wrapper for home page request tests."""

    class_instance = AppHomeView()

    def test_get_home_data_request(self, api_client: APIClient, admin_user: User) -> None:
        """Test if the response as the required keys."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        response = api_client.get(reverse('api:app-home'))
        assert 'unread_notification_count' in response.data
        assert 'daily_appointments' in response.data
        assert 'closest_appointment' in response.data

    def test_get_home_data_return_value(self, api_client: APIClient, admin_user: User, mocker: MockerFixture) -> None:
        """Test the return value of get home data."""
        # fake the current time to avoid crossing over to the next day if the current time is 10pm or later
        now = timezone.make_aware(datetime(2022, 11, 29, 11, 2, 3))
        mock_timezone = mocker.patch('django.utils.timezone.now')
        mock_timezone.return_value = now

        relationship = patient_factories.Relationship(status='CON')
        user_name = relationship.caregiver.user.username
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user_name)
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient, readby=user_name)
        appointment_time = timezone.now() + dt.timedelta(hours=2)
        appointment = factories.LegacyAppointmentFactory(
            patientsernum=patient,
            checkin=1,
            scheduledstarttime=appointment_time,
        )

        response = api_client.get(reverse('api:app-home'))

        assert response.data['unread_notification_count'] == 2
        assert len(response.data['daily_appointments']) == 1
        assert response.data['closest_appointment'] == LegacyAppointmentSerializer(appointment).data

    def test_get_unread_notification_count(self) -> None:
        """Test if function returns number of unread notifications."""
        relationship = patient_factories.Relationship(status='CON')
        user_name = relationship.caregiver.user.username
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient, readby=user_name)
        notifications = models.LegacyNotification.objects.get_unread_queryset(
            patient.patientsernum,
            user_name,
        ).count()
        assert notifications == 2

    def test_get_daily_appointments(self, mocker: MockerFixture) -> None:
        """Test daily appointment according to their dates."""
        relationship = patient_factories.Relationship(status='CON')
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasExpressionFactory(aliassernum=alias)
        # create an appointment close to the end of the day
        appointment = factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
            scheduledstarttime=timezone.make_aware(datetime(2022, 6, 1, 22, 0)),
        )
        factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
            scheduledstarttime=timezone.make_aware(datetime(2022, 6, 2, 0, 1)),
        )

        # mock the current timezone to simulate the UTC time already on the next day
        current_time = datetime(2022, 6, 2, 2, 0, tzinfo=dt.timezone.utc)
        mocker.patch.object(timezone, 'now', return_value=current_time)
        daily_appointments = models.LegacyAppointment.objects.get_daily_appointments(
            relationship.caregiver.user.username,
        )
        assert daily_appointments.count() == 1
        assert daily_appointments[0] == appointment

    def test_get_home_data_with_no_records(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Test the return value of get home data when the fields are empty."""
        relationship = patient_factories.Relationship(status='CON')
        user_name = relationship.caregiver.user.username
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user_name)
        factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)

        response = api_client.get(reverse('api:app-home'))

        assert response.data['unread_notification_count'] == 0
        assert not response.data['daily_appointments']
        assert response.data['closest_appointment'] == LegacyAppointmentSerializer(None).data
