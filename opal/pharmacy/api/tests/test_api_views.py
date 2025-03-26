"""Test module for the REST API endpoints of the `pharmacy` app."""
import json
from pathlib import Path
from uuid import uuid4

from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual
from rest_framework import status
from rest_framework.test import APIClient

from opal.patients.factories import Patient
from opal.pharmacy import models
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default'])

FIXTURES_DIR = Path(__file__).resolve().parents[3].joinpath(
    'core',
    'tests',
    'fixtures',
)
PATIENT_UUID = uuid4()


class TestCreatePharmacyView:
    """Class wrapper for pharmacy endpoint tests."""

    def test_pharmacy_create_unauthenticated(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the requestor is unauthenticated."""
        response = api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': PATIENT_UUID}),
            data=self._load_hl7_fixture('marge_pharmacy.hl7v2'),
        )

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_pharmacy_create_unauthorized(
        self,
        user_api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        response = user_api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': PATIENT_UUID}),
            data=self._load_hl7_fixture('marge_pharmacy.hl7v2'),
        )

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_pharmacy_unsupported_media(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint returns an error if the media type is incorrect."""
        api_client.force_login(interface_engine_user)
        stream = self._load_hl7_fixture('marge_pharmacy.hl7v2')

        response = api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': PATIENT_UUID}),
            data=stream,
        )
        assert 'Unsupported media type' in response.data['detail']
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    def test_pharmacy_create_patient_uuid_does_not_exist(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint returns an error if the patient with given UUID does not exist."""
        api_client.force_login(interface_engine_user)
        data = self._load_hl7_fixture('marge_pharmacy.hl7v2')
        response = api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': PATIENT_UUID}),
            data=data,
            content_type='application/hl7-v2+er7',
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data={
                'detail': 'No Patient matches the given query.',
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pharmacy_create_success(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can create pharmacy for a full input with no errors."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        api_client.force_login(interface_engine_user)

        response = api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': str(patient.uuid)}),
            data=self._load_hl7_fixture('marge_pharmacy.hl7v2'),
            content_type='application/hl7-v2+er7',
        )
        assert models.CodedElement.objects.count() == 11
        assert models.PhysicianPrescriptionOrder.objects.count() == 1
        assert models.PharmacyComponent.objects.count() == 7
        assert models.PharmacyRoute.objects.count() == 1
        assert models.PharmacyEncodedOrder.objects.count() == 1
        assert response.status_code == status.HTTP_201_CREATED

    def test_multiple_pharmacy_create_success(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can create several pharmacy, and re-uses CodedElements."""
        patient = Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        api_client.force_login(interface_engine_user)

        for _ in range(3):
            response = api_client.post(
                reverse('api:patient-pharmacy-create', kwargs={'uuid': str(patient.uuid)}),
                data=self._load_hl7_fixture('marge_pharmacy.hl7v2'),
                content_type='application/hl7-v2+er7',
            )
            assert response.status_code == status.HTTP_201_CREATED

        # CodedElements are get_or_create so this number should not increase (compared to a single POST)
        assert models.CodedElement.objects.count() == 11
        # The rest are tripled compared to the single call in `test_pharmacy_create_success`
        assert models.PhysicianPrescriptionOrder.objects.count() == 3
        assert models.PharmacyComponent.objects.count() == 21
        assert models.PharmacyRoute.objects.count() == 3
        assert models.PharmacyEncodedOrder.objects.count() == 3

    def _load_hl7_fixture(self, filename: str) -> str:
        """Load a HL7 fixture for testing.

        Returns:
            string of the fixture data
        """
        with (FIXTURES_DIR / filename).open('r') as file:
            return file.read()
