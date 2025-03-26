from django.urls import reverse
from django.utils import timezone

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factories
from opal.patients import factories as patient_factories
from opal.patients.models import RelationshipStatus
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


# See similar tests in opal/core/tests/test_drf_permissions.py > TestCaregiverPatientPermissions
class TestCaregiverPermissionsView:
    """Class wrapper for CaregiverPermissionsView tests."""

    def authenticate(self, api_client: APIClient, user: User, appuserid: str = '') -> None:
        """Authenticate a user for testing purposes."""
        api_client.force_authenticate(user=user)
        if appuserid:
            api_client.credentials(HTTP_APPUSERID=appuserid)

    def make_request(self, api_client: APIClient, legacy_id: int) -> Response:
        """
        Make a request to the API view being tested (CaregiverPermissionsView).

        Returns:
            The response of the API call.
        """
        url = reverse('api:caregiver-permissions', kwargs={'legacy_id': legacy_id})
        return api_client.get(url)

    def test_unauthenticated_unauthorized(self, api_client: APIClient, user: User) -> None:
        """Test the request while unauthenticated."""
        caregiver_factories.CaregiverProfile()

        response = self.make_request(api_client, 99)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Authentication' in str(response.data['detail'])

        self.authenticate(api_client, user)

        response = self.make_request(api_client, 99)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'permission_denied' in str(response.data)

    def test_no_caregiver_username(self, api_client: APIClient, listener_user: User) -> None:
        """Test with no provided 'Appuserid'."""
        self.authenticate(api_client, listener_user)
        response = self.make_request(api_client, 99)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "must provide a string 'Appuserid'" in str(response.data['detail'])

    def test_caregiver_not_found(self, api_client: APIClient, listener_user: User) -> None:
        """Test providing a username that doesn't exist."""
        self.authenticate(api_client, listener_user, 'wrong_username')
        response = self.make_request(api_client, 99)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Caregiver not found' in str(response.data['detail'])

    def test_no_relationship(self, api_client: APIClient, listener_user: User) -> None:
        """Test a permissions check where the caregiver doesn't have a relationship with the patient."""
        caregiver = caregiver_factories.CaregiverProfile()
        patient = patient_factories.Patient()

        self.authenticate(api_client, listener_user, caregiver.user.username)
        response = self.make_request(api_client, patient.legacy_id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'does not have a relationship' in str(response.data['detail'])

    def test_unconfirmed_relationship(self, api_client: APIClient, listener_user: User) -> None:
        """Test a permissions check where the caregiver has a relationship with the patient, but it isn't confirmed."""
        relationship = patient_factories.Relationship()

        self.authenticate(api_client, listener_user, relationship.caregiver.user.username)
        response = self.make_request(api_client, relationship.patient.legacy_id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'status is not CONFIRMED' in str(response.data['detail'])

    def test_deceased_patient(self, api_client: APIClient, listener_user: User) -> None:
        """Test that the permission check fails if the patient is deceased."""
        relationship = patient_factories.Relationship(
            status=RelationshipStatus.CONFIRMED,
            patient__date_of_death=timezone.now(),
        )

        self.authenticate(api_client, listener_user, relationship.caregiver.user.username)
        response = self.make_request(api_client, relationship.patient.legacy_id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Patient has a date of death recorded' in str(response.data['detail'])

    def test_success_confirmed_relationship(self, api_client: APIClient, listener_user: User) -> None:
        """Test a permissions check where the caregiver has a confirmed relationship with the patient."""
        relationship = patient_factories.Relationship(status=RelationshipStatus.CONFIRMED)

        self.authenticate(api_client, listener_user, relationship.caregiver.user.username)
        response = self.make_request(api_client, relationship.patient.legacy_id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}  # noqa: WPS520
