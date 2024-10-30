import datetime as dt
from datetime import datetime
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from opal.legacy import factories, models
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.users.models import User

from ...serializers import LegacyAppointmentDetailedSerializer

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestAppAppointmentsView:
    """Class wrapper for appointments request tests."""

    def test_unauthenticated(self, api_client: APIClient) -> None:
        """Unauthenticated requests are forbidden."""
        response = api_client.get(reverse('api:app-appointments'))

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_no_permission(self, api_client: APIClient, user: User) -> None:
        """Requests from an unauthorized user are forbidden."""
        api_client.force_login(user)
        response = api_client.get(reverse('api:app-appointments'))

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_appointment_data_request(self, api_client: APIClient, listener_user: User) -> None:
        """Test if the response as the required keys."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        response = api_client.get(reverse('api:app-appointments'))

        assert 'daily_appointments' in response.data

    def test_get_appointment_data_return_value(
        self,
        api_client: APIClient,
        listener_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Test the return value of get appointment data."""
        # fake the current time to avoid crossing over to the next day if the current time is 10pm or later
        now = timezone.make_aware(datetime(2022, 11, 29, 11, 2, 3))
        mock_timezone = mocker.patch('django.utils.timezone.now')
        mock_timezone.return_value = now

        relationship = patient_factories.Relationship(
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        username = relationship.caregiver.user.username
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=username)
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient)
        factories.LegacyNotificationFactory(patientsernum=patient, readby=username)
        appointment_time = timezone.now() + dt.timedelta(hours=2)
        factories.LegacyAppointmentFactory(patientsernum=patient, checkin=1, scheduledstarttime=appointment_time)
        response = api_client.get(reverse('api:app-appointments'))

        assert len(response.data['daily_appointments']) == 1

    def test_get_daily_appointments(self, mocker: MockerFixture) -> None:
        """Test daily appointment according to their dates."""
        relationship = patient_factories.Relationship(
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
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

    def test_get_appointment_data_from_not_confirmed_patient(self, mocker: MockerFixture) -> None:
        """Test get daily appointment fails from not confirmed patient."""
        relationship = patient_factories.Relationship(
            status=patient_models.RelationshipStatus.PENDING,
        )
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasExpressionFactory(aliassernum=alias)
        # create an appointment close to the end of the day
        factories.LegacyAppointmentFactory(
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

        assert daily_appointments.count() == 0

    def test_get_daily_appointments_details(self, mocker: MockerFixture) -> None:
        """Test daily appointment details."""
        relationship = patient_factories.Relationship(
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        hospital_map = factories.LegacyHospitalMapFactory()
        alias = factories.LegacyAliasFactory(hospitalmapsernum=hospital_map)
        alias_expression = factories.LegacyAliasExpressionFactory(aliassernum=alias)
        # create an appointment close to the end of the day
        factories.LegacyAppointmentFactory(
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
        daily_appointments = LegacyAppointmentDetailedSerializer(
            models.LegacyAppointment.objects.get_daily_appointments(
                relationship.caregiver.user.username,
            ),
            many=True,
        ).data

        assert len(daily_appointments) == 1
        assert 'alias' in daily_appointments[0]
        assert 'aliastype' in daily_appointments[0]['alias']
        assert 'aliasname_en' in daily_appointments[0]['alias']
        assert 'aliasname_fr' in daily_appointments[0]['alias']
        assert 'alias_description_en' in daily_appointments[0]['alias']
        assert 'alias_description_fr' in daily_appointments[0]['alias']
        assert 'appointmentsernum' in daily_appointments[0]
        assert 'checkin' in daily_appointments[0]
        assert 'checkininstruction_en' in daily_appointments[0]
        assert 'checkininstruction_fr' in daily_appointments[0]
        assert 'checkinpossible' in daily_appointments[0]
        assert 'hospitalmap' in daily_appointments[0]
        assert 'mapurl_en' in daily_appointments[0]['hospitalmap']
        assert 'mapurl_fr' in daily_appointments[0]['hospitalmap']
        assert 'mapname_en' in daily_appointments[0]['hospitalmap']
        assert 'mapname_fr' in daily_appointments[0]['hospitalmap']
        assert 'mapdescription_en' in daily_appointments[0]['hospitalmap']
        assert 'mapdescription_fr' in daily_appointments[0]['hospitalmap']
        assert 'patient' in daily_appointments[0]
        assert 'patientsernum' in daily_appointments[0]['patient']
        assert 'first_name' in daily_appointments[0]['patient']
        assert 'last_name' in daily_appointments[0]['patient']
        assert 'roomlocation_en' in daily_appointments[0]
        assert 'roomlocation_fr' in daily_appointments[0]
        assert 'scheduledstarttime' in daily_appointments[0]
        assert 'state' in daily_appointments[0]


class TestUpdateAppointmentCheckinView:
    """Class wrapper for appointment checkin update request tests."""

    def test_unauthenticated(self, api_client: APIClient) -> None:
        """Unauthenticated requests are forbidden."""
        response = api_client.post(reverse('api:patients-legacy-appointment-checkin'))

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_no_permission(self, api_client: APIClient, user: User) -> None:
        """Requests from an unauthorized user are forbidden."""
        api_client.force_login(user)
        response = api_client.post(reverse('api:patients-legacy-appointment-checkin'))

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_update_checkin_success_listener(self, api_client: APIClient, listener_user: User) -> None:
        """Test a successful update of the checkin field."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        medivisit = factories.LegacySourceDatabaseFactory()
        appointment = factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=0,
        )

        response = api_client.post(
            reverse('api:patients-legacy-appointment-checkin'),
            data={
                'source_system_id': '2024A21342134',
                'source_database': medivisit.source_database,
                'checkin': 1,
            },
        )
        appointment.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert response.data
        assert appointment.checkin == 1

    def test_update_checkin_success_orms(self, api_client: APIClient, orms_system_user: User) -> None:
        """Test a successful update of the checkin field."""
        api_client.force_login(user=orms_system_user)
        medivisit = factories.LegacySourceDatabaseFactory()
        appointment = factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=0,
        )

        response = api_client.post(
            reverse('api:patients-legacy-appointment-checkin'),
            data={
                'source_system_id': '2024A21342134',
                'source_database': medivisit.source_database,
                'checkin': 1,
            },
        )
        appointment.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert response.data
        assert appointment.checkin == 1

    def test_update_checkin_multiple_found(self, api_client: APIClient, listener_user: User) -> None:
        """Test response of finding multiple appointments matching search."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        medivisit = factories.LegacySourceDatabaseFactory()
        appointment1 = factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=0,
        )
        appointment2 = factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=1,
        )

        response = api_client.post(
            reverse('api:patients-legacy-appointment-checkin'),
            data={
                'source_system_id': '2024A21342134',
                'source_database': medivisit.source_database,
                'checkin': 1,
            },
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert appointment1.checkin == 0
        assert appointment2.checkin == 1
        assert 'Cannot find a unique appointment matching criteria' in response.data['detail']

    def test_update_checkin_invalid_checkin_value(self, api_client: APIClient, listener_user: User) -> None:
        """Test response of supplying invalid checkin value to endpoint."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        medivisit = factories.LegacySourceDatabaseFactory()
        appointment1 = factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=0,
        )

        response = api_client.post(
            reverse('api:patients-legacy-appointment-checkin'),
            data={
                'source_system_id': '2024A21342134',
                'source_database': medivisit.source_database,
                'checkin': 2,
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert appointment1.checkin == 0
        assert 'Must be a valid boolean.' in response.data['checkin']

    def test_update_checkin_missing_sourcedb(self, api_client: APIClient, listener_user: User) -> None:
        """Test response of sending incomplete data to endpoint."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        medivisit = factories.LegacySourceDatabaseFactory()
        factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=0,
        )

        response = api_client.post(
            reverse('api:patients-legacy-appointment-checkin'),
            data={
                'source_system_id': '2024A21342134',
                'checkin': 1,
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert 'This field is required.' in response.data['source_database']

    def test_update_checkin_missing_sourceid(self, api_client: APIClient, listener_user: User) -> None:
        """Test response of sending incomplete data to endpoint."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        medivisit = factories.LegacySourceDatabaseFactory()
        factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=0,
        )

        response = api_client.post(
            reverse('api:patients-legacy-appointment-checkin'),
            data={
                'source_database': medivisit.source_database,
                'checkin': 1,
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert 'This field is required.' in response.data['source_system_id']

    def test_update_checkin_missing_checkin(self, api_client: APIClient, listener_user: User) -> None:
        """Test response of sending missing checkin field data to endpoint."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        medivisit = factories.LegacySourceDatabaseFactory()
        appointment1 = factories.LegacyAppointmentFactory(
            source_system_id='2024A21342134',
            source_database=medivisit,
            checkin=0,
        )

        response = api_client.post(
            reverse('api:patients-legacy-appointment-checkin'),
            data={
                'source_system_id': '2024A21342134',
                'source_database': medivisit.source_database,
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert appointment1.checkin == 0
        assert 'This field is required.' in response.data['checkin']
