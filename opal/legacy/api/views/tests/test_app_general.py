from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.legacy import factories, models
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestGeneralAppView:
    """Class wrapper for general page request tests."""

    def test_get_general_data_request(self, api_client: APIClient, admin_user: User) -> None:
        """Test if the response as the required keys."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        response = api_client.get(reverse('api:app-general'))
        assert 'unread_announcement_count' in response.data

    def test_get_request_related_to_patient(self, api_client: APIClient, admin_user: User) -> None:
        """Test if the response data belong to the request patient."""
        patient = factories.LegacyPatientFactory()
        user = factories.LegacyUserFactory(usertypesernum=patient.patientsernum)
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        response = api_client.get(reverse('api:app-general'))
        assert user.usertypesernum == patient.patientsernum
        assert 'unread_announcement_count' in response.data

    def test_get_unread_announcement_count(self) -> None:
        """Test if function returns number of unread announcement."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyAnnouncementFactory(patientsernum=patient)
        factories.LegacyAnnouncementFactory(patientsernum=patient)
        factories.LegacyAnnouncementFactory(patientsernum=patient, readstatus=1)
        announcements = models.LegacyAnnouncement.objects.get_unread_queryset(patient.patientsernum).count()
        assert announcements == 2
