from datetime import datetime

from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.asserts import assertContains
from rest_framework.test import APIClient

from opal.legacy import factories, models
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.users import factories as user_factories
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
        assert announcements == 2

    def test_get_unread_announcement_multiple_patient(self) -> None:
        """Test the return of announcements for multiple patient without duplicate 'postcontrolsernum'."""
        marge_patient = factories.LegacyPatientFactory()
        homer_patient = factories.LegacyPatientFactory(
            patientsernum=52,
            first_name='Homer',
            ramq='SIMH12345678',
            email='homer@opalmedapps.ca',
        )
        post_control = factories.LegacyPostcontrolFactory(posttype='Announcement')
        user = factories.LegacyUserFactory()
        factories.LegacyAnnouncementFactory(patientsernum=marge_patient, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=homer_patient, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=marge_patient)
        factories.LegacyAnnouncementFactory(patientsernum=homer_patient, readby=[user.username])
        announcements = models.LegacyAnnouncement.objects.get_unread_queryset(
            [marge_patient.patientsernum],
            user.username,
        )
        assert announcements == 2

    def test_get_unread_announcement_nothing(self) -> None:
        """Test the return of zero announcements when nothing is available."""
        marge_patient = factories.LegacyPatientFactory()
        homer_patient = factories.LegacyPatientFactory(
            patientsernum=52,
            first_name='Homer',
            ramq='SIMH12345678',
            email='homer@opalmedapps.ca',
        )
        post_control = factories.LegacyPostcontrolFactory(posttype='Announcement')
        user = factories.LegacyUserFactory()
        factories.LegacyAnnouncementFactory(patientsernum=marge_patient, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=homer_patient, postcontrolsernum=post_control)
        factories.LegacyAnnouncementFactory(patientsernum=marge_patient)
        factories.LegacyAnnouncementFactory(patientsernum=marge_patient, readby=[user.username])
        announcements = models.LegacyAnnouncement.objects.get_unread_queryset([125], user.username)
        assert announcements == 0

    def test_app_general_get_unread_announcement_count(  # noqa: WPS213
        self,
        api_client: APIClient,
        listener_user: User,
    ) -> None:
        """Ensure `api:app-general` returns unread announcements counts only for the confirmed relationships."""
        # Create legacy Marge patient/user
        factories.LegacyUserFactory(usersernum=99, usertypesernum=99, username='marge_username')
        legacy_marge_patient = factories.LegacyPatientFactory(
            patientsernum=99,
            ramq='SIMM11111111',
            first_name='Marge',
            last_name='Simpson',
            tel_num='5149995555',
            email='marge@opalmedapps.ca',
        )
        factories.LegacyPatientControlFactory(patient=legacy_marge_patient)
        django_marge_patient = patient_factories.Patient(
            legacy_id=legacy_marge_patient.patientsernum,
            ramq=legacy_marge_patient.ramq,
            first_name=legacy_marge_patient.first_name,
            last_name=legacy_marge_patient.last_name,
            date_of_birth=timezone.make_aware(datetime(2018, 1, 1)),
        )
        marge_user = user_factories.Caregiver(email=legacy_marge_patient.email, username='marge_username')
        marge_caregiver = patient_factories.CaregiverProfile(
            legacy_id=legacy_marge_patient.patientsernum,
            user=marge_user,
        )
        patient_factories.Relationship(
            patient=django_marge_patient,
            caregiver=marge_caregiver,
            type=patient_models.RelationshipType.objects.self_type(),
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        # Create legacy Homer patient/user
        factories.LegacyUserFactory(usersernum=98, usertypesernum=99, username='homer_username')
        legacy_homer_patient = factories.LegacyPatientFactory(
            patientsernum=98,
            ramq='SIMH22222222',
            first_name='Homer',
            last_name='Simpson',
            tel_num='5149994444',
            email='homer@opalmedapps.ca',
        )
        factories.LegacyPatientControlFactory(patient=legacy_homer_patient)
        django_homer_patient = patient_factories.Patient(
            legacy_id=legacy_homer_patient.patientsernum,
            ramq=legacy_homer_patient.ramq,
            first_name=legacy_homer_patient.first_name,
            last_name=legacy_homer_patient.last_name,
            date_of_birth=timezone.make_aware(datetime(2018, 1, 1)),
        )
        homer_caregiver = patient_factories.CaregiverProfile(
            legacy_id=legacy_homer_patient.patientsernum,
            user=user_factories.Caregiver(email=legacy_homer_patient.email, username='homer_username'),
        )
        patient_factories.Relationship(
            patient=django_homer_patient,
            caregiver=homer_caregiver,
            type=patient_models.RelationshipType.objects.self_type(),
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        patient_factories.Relationship(
            patient=django_homer_patient,
            caregiver=marge_caregiver,
            type=patient_models.RelationshipType.objects.guardian_caregiver(),
            status=patient_models.RelationshipStatus.CONFIRMED,
        )

        # Create legacy Bart patient/user
        factories.LegacyUserFactory(usersernum=97, usertypesernum=99, username='homer_username')
        legacy_bart_patient = factories.LegacyPatientFactory(
            patientsernum=97,
            ramq='SIMB33333333',
            first_name='Bart',
            last_name='Simpson',
            tel_num='5149993333',
            email='bart@opalmedapps.ca',
        )
        factories.LegacyPatientControlFactory(patient=legacy_bart_patient)
        django_bart_patient = patient_factories.Patient(
            legacy_id=legacy_bart_patient.patientsernum,
            ramq=legacy_bart_patient.ramq,
            first_name=legacy_bart_patient.first_name,
            last_name=legacy_bart_patient.last_name,
            date_of_birth=timezone.make_aware(datetime(2018, 1, 1)),
        )
        bart_caregiver = patient_factories.CaregiverProfile(
            legacy_id=legacy_bart_patient.patientsernum,
            user=user_factories.Caregiver(email=legacy_bart_patient.email, username='bart_username'),
        )
        patient_factories.Relationship(
            patient=django_bart_patient,
            caregiver=bart_caregiver,
            type=patient_models.RelationshipType.objects.self_type(),
            status=patient_models.RelationshipStatus.CONFIRMED,
        )
        patient_factories.Relationship(
            patient=django_bart_patient,
            caregiver=marge_caregiver,
            type=patient_models.RelationshipType.objects.guardian_caregiver(),
            status=patient_models.RelationshipStatus.PENDING,
        )

        factories.LegacyAnnouncementFactory(patientsernum=legacy_marge_patient)
        factories.LegacyAnnouncementFactory(patientsernum=legacy_homer_patient)
        factories.LegacyAnnouncementFactory(patientsernum=legacy_homer_patient)
        factories.LegacyAnnouncementFactory(patientsernum=legacy_bart_patient)

        api_client.force_login(user=listener_user)
        api_client.credentials(HTTP_APPUSERID=marge_user.username)
        response = api_client.get(reverse('api:app-general'))

        assert models.LegacyAnnouncement.objects.count() == 4

        assertContains(
            response=response,
            text='{"unread_announcement_count":3}',
        )
