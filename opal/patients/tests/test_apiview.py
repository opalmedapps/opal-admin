"""Test module for registration api endpoints."""

from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.db.models import Prefetch
from django.urls import reverse

from rest_framework.test import APIClient

from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus
from opal.hospital_settings.models import Institution


def test_get_caregiver_patient_list_no_patient(api_client: APIClient, admin_user: AbstractUser) -> None:
    """Test patient list endpoint to return an empty list if there is no relationship."""
    api_client.force_login(user=admin_user)

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).filter(status=RegistrationCodeStatus.NEW)
    )

    print(queryset.)

    assert 1 == 2
