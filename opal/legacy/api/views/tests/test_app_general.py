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
        user = factories.LegacyUserFactory()
        factories.LegacyAnnouncementFactory(patientsernum=patient)
        factories.LegacyAnnouncementFactory(patientsernum=patient)
        factories.LegacyAnnouncementFactory(patientsernum=patient, readby=[user.username])
        announcements = models.LegacyAnnouncement.objects.get_unread_queryset([patient.patientsernum], user.username)
        assert announcements == 3

    def test_get_unread_announcement_multiple_patient(self) -> None:
        """Test the return of announcements for multiple patient without dupicate 'postcontrolsernum'."""
        patient1 = factories.LegacyPatientFactory()
        patient2 = factories.LegacyPatientFactory()
        post_control = factories.LegacyPostcontrolFactory(posttype='Announcement')
        user = factories.LegacyUserFactory()
        factories.LegacyAnnouncementFactory(patientsernum=patient1, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=patient2, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=patient1)
        factories.LegacyAnnouncementFactory(patientsernum=patient1, readby=[user.username])
        announcements = models.LegacyAnnouncement.objects.get_unread_queryset([patient1.patientsernum], user.username)
        assert announcements == 4

    def test_get_unread_announcement_nothing(self) -> None:
        """Test the return of zero announcements when nothing is available."""
        patient1 = factories.LegacyPatientFactory()
        patient2 = factories.LegacyPatientFactory()
        post_control = factories.LegacyPostcontrolFactory(posttype='Announcement')
        user = factories.LegacyUserFactory()
        factories.LegacyAnnouncementFactory(patientsernum=patient1, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=patient2, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=patient1)
        factories.LegacyAnnouncementFactory(patientsernum=patient1, readby=[user.username])
        announcements = models.LegacyAnnouncement.objects.get_unread_queryset([125], user.username)
        assert announcements == 0
