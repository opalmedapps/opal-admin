from datetime import datetime

from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from opal.users.models import User

from .. import factories, models
from ..api.views.app_home import AppHomeView

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

    def test_get_home_data_return_value(self, api_client: APIClient, admin_user: User) -> None:
        """Test the return value of get home data."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        factories.LegacyPatientFactory()
        patient = models.LegacyPatient.objects.all()[0]
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient, readstatus=1)
        appointment_time = timezone.now() + timezone.timedelta(hours=2)
        factories.LegacyAppointmentFactory(patientsernum=patient, checkin=1, scheduledstarttime=appointment_time)

        response = api_client.get(reverse('api:app-home'))
        assert response.data['unread_notification_count'] == 2
        assert len(response.data['daily_appointments']) == 1

    def test_get_unread_notification_count(self) -> None:
        """Test if function returns number of unread notifications."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient, readstatus=1)
        notifications = self.class_instance.get_unread_notification_count(patient.patientsernum)
        assert notifications == 2

    def test_get_daily_appointments(self, mocker: MockerFixture) -> None:
        """Test daily appointment according to their dates."""
        patient = factories.LegacyPatientFactory()
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasexpressionFactory(aliassernum=alias)
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
        current_time = datetime(2022, 6, 2, 2, 0, tzinfo=timezone.utc)
        mocker.patch.object(timezone, 'now', return_value=current_time)
        daily_appointments = self.class_instance.get_daily_appointments(patient.patientsernum)

        assert daily_appointments.count() == 1
        assert daily_appointments[0] == appointment
