from datetime import datetime
from typing import Any

from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factories
from opal.patients import factories as patient_factories
from opal.patients.models import RelationshipStatus
from opal.users.models import User

from .. import factories, models
from ..api import views

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestHomeAppView:
    """Class wrapper for home page request tests."""

    class_instance = views.AppHomeView()

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
        notifications = models.LegacyNotification.objects.get_unread_queryset(patient.patientsernum).count()
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
        daily_appointments = models.LegacyAppointment.objects.get_daily_appointments(patient.patientsernum)

        assert daily_appointments.count() == 1
        assert daily_appointments[0] == appointment


class TestChartAppView:
    """
    Class wrapper for chart page request tests.

    PatientSernum 51 is define in the legacy databse by DBV script for testing purpose.
    """

    def test_get_chart_data_request(self, api_client: APIClient, admin_user: User) -> None:
        """Test if the response as the required keys."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        response = api_client.get(reverse('api:app-chart', kwargs={'legacy_id': 51}))
        assert 'unread_appointment_count' in response.data
        assert 'unread_document_count' in response.data
        assert 'unread_txteammessage_count' in response.data
        assert 'unread_educationalmaterial_count' in response.data
        assert 'unread_questionnaire_count' in response.data

    def test_get_unread_appointment_count(self) -> None:
        """Test if function returns number of unread appointments."""
        patient = factories.LegacyPatientFactory()
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasexpressionFactory(aliassernum=alias)

        factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )
        factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )
        factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
            readstatus=1,
        )

        appointments = models.LegacyAppointment.objects.get_unread_queryset(patient.patientsernum).count()
        assert appointments == 2

    def test_get_unread_txteammessage_count(self) -> None:
        """Test if function returns number of unread txteammessages."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyTxTeamMessageFactory(patientsernum=patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=patient, readstatus=1)
        txteammessages = models.LegacyTxTeamMessage.objects.get_unread_queryset(patient.patientsernum).count()
        assert txteammessages == 2

    def test_get_unread_edumaterial_count(self) -> None:
        """Test if function returns number of unread educational materials."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyEducationalMaterialFactory(patientsernum=patient)
        factories.LegacyEducationalMaterialFactory(patientsernum=patient)
        factories.LegacyEducationalMaterialFactory(patientsernum=patient, readstatus=1)
        edumaterials = models.LegacyEducationalMaterial.objects.get_unread_queryset(patient.patientsernum).count()
        assert edumaterials == 2

    def test_get_unread_questionnaire_count(self) -> None:
        """Test if function returns number of unread questionnaires."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyQuestionnaireFactory(patientsernum=patient)
        factories.LegacyQuestionnaireFactory(patientsernum=patient)
        factories.LegacyQuestionnaireFactory(patientsernum=patient, completedflag=1)
        questionnaires = models.LegacyQuestionnaire.objects.get_unread_queryset(patient.patientsernum).count()
        assert questionnaires == 2


# See similar tests in opal/core/tests/test_drf_permissions.py > TestCaregiverPatientPermissions
class TestCaregiverPermissionsView:
    """Class wrapper for CaregiverPermissionsView tests."""

    def authenticate(self, api_client: APIClient, admin_user: User, appuserid: str = '') -> None:
        """Authenticate a user for testing purposes."""
        api_client.force_authenticate(user=admin_user)
        if appuserid:
            api_client.credentials(HTTP_APPUSERID=appuserid)

    def make_request(self, api_client: APIClient, legacy_id: int) -> Any:
        """
        Make a request to the API view being tested (CaregiverPermissionsView).

        Returns:
            The response of the API call.
        """
        url = reverse('api:caregiver-permissions', kwargs={'legacy_id': legacy_id})
        return api_client.get(url)

    def test_unauthenticated(self, api_client: APIClient, admin_user: User) -> None:
        """Test the request while unauthenticated."""
        caregiver_factories.CaregiverProfile()

        response = self.make_request(api_client, 99)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Authentication' in str(response.data['detail'])

    def test_no_caregiver_username(self, api_client: APIClient, admin_user: User) -> None:
        """Test with no provided 'Appuserid'."""
        caregiver_factories.CaregiverProfile()

        self.authenticate(api_client, admin_user)
        response = self.make_request(api_client, 99)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "must provide a string 'Appuserid'" in str(response.data['detail'])

    def test_caregiver_not_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a username that doesn't exist."""
        caregiver_factories.CaregiverProfile()

        self.authenticate(api_client, admin_user, 'wrong_username')
        response = self.make_request(api_client, 99)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Caregiver not found' in str(response.data['detail'])

    def test_no_relationship(self, api_client: APIClient, admin_user: User) -> None:
        """Test a permissions check where the caregiver doesn't have a relationship with the patient."""
        caregiver = caregiver_factories.CaregiverProfile()
        patient = patient_factories.Patient()

        self.authenticate(api_client, admin_user, caregiver.user.username)
        response = self.make_request(api_client, patient.legacy_id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'does not have a relationship' in str(response.data['detail'])

    def test_unconfirmed_relationship(self, api_client: APIClient, admin_user: User) -> None:
        """Test a permissions check where the caregiver has a relationship with the patient, but it isn't confirmed."""
        relationship = patient_factories.Relationship()

        self.authenticate(api_client, admin_user, relationship.caregiver.user.username)
        response = self.make_request(api_client, relationship.patient.legacy_id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'status is not CONFIRMED' in str(response.data['detail'])

    def test_success_confirmed_relationship(self, api_client: APIClient, admin_user: User) -> None:
        """Test a permissions check where the caregiver has a confirmed relationship with the patient."""
        relationship = patient_factories.Relationship(status=RelationshipStatus.CONFIRMED)

        self.authenticate(api_client, admin_user, relationship.caregiver.user.username)
        response = self.make_request(api_client, relationship.patient.legacy_id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}  # noqa: WPS520
