"""Test module for the REST API endpoints of the `pharmacy` app."""
from pathlib import Path
from uuid import uuid4

from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains
from rest_framework import status
from rest_framework.test import APIClient

from opal.hospital_settings import factories as hospital_factories
from opal.hospital_settings.models import Site
from opal.patients import factories as patient_factories
from opal.pharmacy import models
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default'])

FIXTURES_DIR = Path(__file__).resolve().parents[3].joinpath(
    'core',
    'tests',
    'fixtures',
)
PATIENT_UUID = uuid4()


class TestCreatePrescriptionView:  # noqa: WPS338
    """Class wrapper for pharmacy endpoint tests."""

    @pytest.fixture(autouse=True)
    def _before_each(self) -> None:
        """Fixture for pre-creating the valid site acronyms for the pytest env."""
        hospital_factories.Site(acronym='RVH')
        hospital_factories.Site(acronym='MGH')
        hospital_factories.Site(acronym='MCH')
        hospital_factories.Site(acronym='LAC')

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

    def test_pharmacy_create_success(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can create pharmacy for a full input with no errors."""
        patient = patient_factories.Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        patient_factories.HospitalPatient(
            patient=patient,
            site=Site.objects.get(acronym='RVH'),
            mrn='9999996',
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

    def test_pharmacy_missing_coded_elements_create_success(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can create pharmacy for an input missing optional CE elements with no errors."""
        patient = patient_factories.Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        patient_factories.HospitalPatient(
            patient=patient,
            site=Site.objects.get(acronym='RVH'),
            mrn='9999996',
        )
        api_client.force_login(interface_engine_user)

        response = api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': str(patient.uuid)}),
            data=self._load_hl7_fixture('marge_missing_CE_pharmacy.hl7v2'),
            content_type='application/hl7-v2+er7',
        )

        assert models.CodedElement.objects.count() == 0
        assert models.PhysicianPrescriptionOrder.objects.count() == 1
        assert models.PharmacyComponent.objects.count() == 1
        assert models.PharmacyRoute.objects.count() == 1
        assert models.PharmacyEncodedOrder.objects.count() == 1
        assert response.status_code == status.HTTP_201_CREATED

    def test_multiple_pharmacy_create_success(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can create several pharmacy, and re-uses CodedElements."""
        patient = patient_factories.Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        patient_factories.HospitalPatient(
            patient=patient,
            site=Site.objects.get(acronym='RVH'),
            mrn='9999996',
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

    def test_pharmacy_route_to_internal_value(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure administration_method is properly None-ed if all subfields are blank."""
        patient = patient_factories.Patient(
            ramq='TEST01161972',
            uuid=PATIENT_UUID,
        )
        patient_factories.HospitalPatient(
            patient=patient,
            site=Site.objects.get(acronym='MGH'),
            mrn='9999998',
        )
        api_client.force_login(interface_engine_user)
        #  Homer's pharmacy example has the case of blank administration_method subfields in RXR
        response = api_client.post(
            reverse('api:patient-pharmacy-create', kwargs={'uuid': str(patient.uuid)}),
            data=self._load_hl7_fixture('homer_pharmacy.hl7v2'),
            content_type='application/hl7-v2+er7',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert not response.data['pharmacy_encoded_order']['pharmacy_route']['administration_method']  # noqa: E501

    def _load_hl7_fixture(self, filename: str) -> str:
        """Load a HL7 fixture for testing.

        Returns:
            string of the fixture data
        """
        with (FIXTURES_DIR / filename).open('r') as file:
            return file.read()
