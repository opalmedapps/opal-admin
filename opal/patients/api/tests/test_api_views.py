"""Test module for the `patients` app REST API endpoints."""
import json
from collections.abc import Callable
from datetime import datetime
from http import HTTPStatus
from typing import Any

from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual, assertRaisesMessage
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient

from opal.caregivers.factories import CaregiverProfile, Device, RegistrationCode
from opal.hospital_settings.factories import Institution, Site
from opal.patients import models as patient_models
from opal.patients.factories import HospitalPatient, Patient, Relationship, RelationshipType
from opal.users import factories as caregiver_factories
from opal.users.models import User
from opal.patients.api.views import CaregiverRelationshipView

pytestmark = pytest.mark.django_db(databases=['default'])


def test_my_caregiver_list_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    listener_user: User,
) -> None:
    """Ensure that the API to create quantity samples requires an authenticated user."""
    patient = Patient()
    url = reverse('api:caregivers-list', kwargs={'legacy_id': patient.legacy_id})

    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(listener_user)

    response = api_client.options(url)

    # the CaregiverSelfPermissions permission is reporting the missing header
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'Appuserid' in response.content.decode()


def test_my_caregiver_list(api_client: APIClient, admin_user: User) -> None:
    """Test the return of the caregivers list for a given patient."""
    api_client.force_login(user=admin_user)
    patient = Patient()
    caregiver1 = CaregiverProfile()
    caregiver2 = CaregiverProfile()
    relationship1 = Relationship(patient=patient, caregiver=caregiver1)
    relationship2 = Relationship(
        patient=patient,
        caregiver=caregiver2,
        status=patient_models.RelationshipStatus.CONFIRMED,
        type=patient_models.RelationshipType.objects.self_type(),
    )
    api_client.credentials(HTTP_APPUSERID=caregiver2.user.username)

    response = api_client.get(reverse(
        'api:caregivers-list',
        kwargs={'legacy_id': patient.legacy_id},
    ))

    assert response.status_code == HTTPStatus.OK
    assert response.json()[0] == {
        'caregiver_id': caregiver1.user.id,
        'first_name': caregiver1.user.first_name,
        'last_name': caregiver1.user.last_name,
        'status': relationship1.status,
        'relationship_type': relationship1.type.name,
    }
    assert response.json()[1] == {
        'caregiver_id': caregiver2.user.id,
        'first_name': caregiver2.user.first_name,
        'last_name': caregiver2.user.last_name,
        'status': relationship2.status,
        'relationship_type': relationship2.type.name,
    }


def test_my_caregiver_list_failure(api_client: APIClient, admin_user: User) -> None:
    """Test the failure of the caregivers list for a given patient."""
    api_client.force_login(user=admin_user)
    patient = Patient()
    caregiver1 = CaregiverProfile()
    caregiver2 = CaregiverProfile()
    Relationship(patient=patient, caregiver=caregiver1)
    Relationship(patient=patient, caregiver=caregiver2)
    api_client.credentials(HTTP_APPUSERID=caregiver1.user.username)

    response = api_client.get(reverse(
        'api:caregivers-list',
        kwargs={'legacy_id': 1654161},
    ))
    assert response.data['detail'] == 'Caregiver does not have a relationship with the patient.'
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_caregiver_list_swagger_fake_view(api_client: APIClient, admin_user: User) -> None:
    """Test the response when swagger_fake_view is True."""
    api_client.force_login(user=admin_user)
    view = CaregiverRelationshipView()
    view.swagger_fake_view = True  # type: ignore[attr-defined]
    view.kwargs = {'legacy_id': 1}
    queryset = view.get_queryset()

    assert queryset.count() == 0, "The queryset should be empty when swagger_fake_view is True."


class TestRetrieveRegistrationDetailsView:
    """A class to test RetrieveRegistrationDetails apis."""

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        registration_listener_user: User,
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:registration-code', kwargs={'code': '123456'})

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(registration_listener_user)
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_api_retrieve_registration(self, api_client: APIClient, admin_user: User) -> None:
        """Test api registration code with summary serializer."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        relationship = Relationship(patient=patient)
        registration_code = RegistrationCode(relationship=relationship)

        # Build relationships: hospital_patient -> site -> institution
        institution = Institution()
        site = Site(institution=institution)
        hospital_patient = HospitalPatient(patient=patient, site=site)

        response = api_client.get(reverse(
            'api:registration-code',
            kwargs={'code': registration_code.code},
        ))
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            'caregiver': {
                'first_name': relationship.caregiver.user.first_name,
                'last_name': relationship.caregiver.user.last_name,
            },
            'patient': {
                'first_name': hospital_patient.patient.first_name,
                'last_name': hospital_patient.patient.last_name,
            },
            'institution': {
                'id': institution.id,
                'name': institution.name,
            },
        }

    def test_api_not_retrieve_deceased_patient(self, api_client: APIClient, admin_user: User) -> None:
        """Test api registration code with summary serializer not retrieve deceased patient."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        date_of_death = timezone.make_aware(datetime(2099, 9, 27))
        patient = Patient(date_of_death=date_of_death)
        relationship = Relationship(patient=patient)
        registration_code = RegistrationCode(relationship=relationship)

        response = api_client.get(reverse(
            'api:registration-code',
            kwargs={'code': registration_code.code},
        ))
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json() == {'detail': 'You do not have permission to perform this action.'}


class TestPatientDemographicView:
    """Class wrapper for patient demographic endpoint tests."""

    def test_demographic_update_unauthenticated(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthenticated."""
        response = api_client.put(reverse('api:patient-demographic-update'))

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

        response = api_client.patch(reverse('api:patient-demographic-update'))

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_demographic_update_unauthorized(
        self,
        user_api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        response = user_api_client.put(reverse('api:patient-demographic-update'))

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

        response = user_api_client.patch(reverse('api:patient-demographic-update'))

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_demographic_update_with_empty_mrns(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint returns an error if the MRNs list is empty."""
        api_client.force_login(interface_engine_user)
        data = self._get_valid_input_data()
        data['mrns'] = []

        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=data,
        )

        assertContains(
            response=response,
            text='This list may not be empty.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=data,
        )

        assertContains(
            response=response,
            text='This list may not be empty.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_demographic_update_invalid_mrns(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint returns an error if the MRNs list dictionaries are invalid."""
        api_client.force_login(interface_engine_user)
        data = self._get_valid_input_data()
        data['mrns'] = [
            {'site': 'RVH', 'mrn_error': '9999996', 'is_active_erorr': True},
        ]

        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=data,
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=[{
                'mrn': ['This field is required.'],
                'is_active': ['This field is required.'],
                'site_code': ['This field is required.'],
            }],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data['mrns'] = [
            {'mrn': '9999996', 'is_active': True},
        ]

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=data,
        )

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=[{
                'site_code': ['This field is required.'],
            }],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_demographic_update_with_invalid_sites(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint returns an error if provided sites do not exist."""
        api_client.force_login(interface_engine_user)

        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=[
                {
                    'site_code': ['Provided "RVH" site acronym does not exist.'],
                },
                {
                    'site_code': ['Provided "MGH" site acronym does not exist.'],
                },
            ],
        )

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=[
                {
                    'site_code': ['Provided "RVH" site acronym does not exist.'],
                },
                {
                    'site_code': ['Provided "MGH" site acronym does not exist.'],
                },
            ],
        )

    def test_demographic_update_mrn_site_pairs_do_not_exist(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint raises a NotFound exception if provided MRN/site pairs do not exist."""
        Site(acronym='RVH')
        Site(acronym='MGH')

        api_client.force_login(interface_engine_user)

        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assertRaisesMessage(
            expected_exception=NotFound,
            expected_message='{0} {1}'.format(
                'Cannot find patient record with the provided MRNs and sites.',
                'Make sure that MRN/site pairs refer to the same patient.',
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assertRaisesMessage(
            expected_exception=NotFound,
            expected_message='{0} {1}'.format(
                'Cannot find patient record with the provided MRNs and sites.',
                'Make sure that MRN/site pairs refer to the same patient.',
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_demographic_update_different_patients_error(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint raises a NotFound exception if MRNs referring to different patients."""
        patient_one = Patient()
        patient_two = Patient(ramq='TEST01161972')

        HospitalPatient(
            patient=patient_one,
            mrn='9999996',
            site=Site(acronym='RVH'),
        )
        HospitalPatient(
            patient=patient_two,
            mrn='9999997',
            site=Site(acronym='MGH'),
        )

        api_client.force_login(interface_engine_user)

        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assertRaisesMessage(
            expected_exception=NotFound,
            expected_message='{0} {1}'.format(
                'Cannot find patient record with the provided MRNs and sites.',
                'Make sure that MRN/site pairs refer to the same patient.',
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assertRaisesMessage(
            expected_exception=NotFound,
            expected_message='{0} {1}'.format(
                'Cannot find patient record with the provided MRNs and sites.',
                'Make sure that MRN/site pairs refer to the same patient.',
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_demographic_update_success(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can update patient info with no errors."""
        patient = Patient(ramq='TEST01161972')

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
        )

        HospitalPatient(
            patient=patient,
            mrn='9999996',
            site=Site(acronym='RVH'),
        )
        HospitalPatient(
            patient=patient,
            mrn='9999997',
            site=Site(acronym='MGH'),
        )

        api_client.force_login(interface_engine_user)
        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

    def test_demographic_update_no_relationship(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint can update patient info when the patient does not have a self relationship (no user)."""
        rvh_site = Site(acronym='RVH')
        mgh_site = Site(acronym='MGH')
        patient = Patient(ramq='TEST01161972')

        HospitalPatient(
            patient=patient,
            mrn='9999996',
            site=rvh_site,
        )
        HospitalPatient(
            patient=patient,
            mrn='9999997',
            site=mgh_site,
        )

        api_client.force_login(interface_engine_user)
        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

    def test_demographic_update_deceased_patient(
        self,
        api_client: APIClient,
        interface_engine_user: User,
    ) -> None:
        """Ensure the endpoint keeps the relationships as is."""
        patient = Patient(ramq='TEST01161972')

        Relationship(
            patient=patient,
            type=patient_models.RelationshipType.objects.self_type(),
            status=patient_models.RelationshipStatus.CONFIRMED,
        ).save()
        Relationship(
            patient=patient,
            caregiver=CaregiverProfile(),
            type=patient_models.RelationshipType.objects.guardian_caregiver(),
        ).save()

        HospitalPatient(
            patient=patient,
            mrn='9999996',
            site=Site(acronym='RVH'),
        )
        HospitalPatient(
            patient=patient,
            mrn='9999997',
            site=Site(acronym='MGH'),
        )

        api_client.force_login(interface_engine_user)
        payload = self._get_valid_input_data()
        payload['date_of_death'] = datetime.now().replace(
            microsecond=0,
        ).astimezone().isoformat()

        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=payload,
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=payload,
        )

        relationships = patient_models.Relationship.objects.all()
        # the relationship status stays untouched
        assert relationships[0].status == patient_models.RelationshipStatus.CONFIRMED
        assert relationships[1].status == patient_models.RelationshipStatus.PENDING
        assert relationships[0].end_date is not None
        assert relationships[0].end_date > datetime.now().date()
        assert relationships[1].end_date is not None
        assert relationships[1].end_date > datetime.now().date()

    def _get_valid_input_data(self) -> dict[str, Any]:
        """Generate valid JSON data for the patient demographic update.

        Returns:
            dict: valid JSON data
        """
        return {
            'mrns': [
                {'site_code': 'RVH', 'mrn': '9999996', 'is_active': True},
                {'site_code': 'MGH', 'mrn': '9999997', 'is_active': True},
            ],
            'ramq': 'TEST01161972',
            'first_name': 'Lisa',
            'last_name': 'Phillips',
            'date_of_birth': '1973-01-16',
            'date_of_death': None,
            'sex': 'F',
        }


class TestPatientCaregiverDevicesView:
    """Class wrapper for patient caregiver devices endpoint tests."""

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        legacy_backend_user: User,
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:patient-caregiver-devices', kwargs={'legacy_id': 1})

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(legacy_backend_user)
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_get_patient_caregivers_success(self, api_client: APIClient, admin_user: User) -> None:
        """Test get patient caregiver devices success."""
        api_client.force_login(user=admin_user)

        patient = Patient()

        user1 = caregiver_factories.Caregiver(language='en', phone_number='+11234567890')
        user2 = caregiver_factories.Caregiver(language='fr', phone_number='+11234567891')
        caregiver1 = CaregiverProfile(user=user1)
        caregiver2 = CaregiverProfile(user=user2)
        Relationship(caregiver=caregiver1, patient=patient, status=patient_models.RelationshipStatus.CONFIRMED)
        Relationship(caregiver=caregiver2, patient=patient, status=patient_models.RelationshipStatus.CONFIRMED)
        Relationship(patient=patient, caregiver=caregiver1, status=patient_models.RelationshipStatus.EXPIRED)
        Relationship(patient=patient, status=patient_models.RelationshipStatus.PENDING)
        device1 = Device(caregiver=caregiver1)
        device2 = Device(caregiver=caregiver2)
        institution = Institution()

        response = api_client.get(reverse(
            'api:patient-caregiver-devices',
            kwargs={'legacy_id': patient.legacy_id},
        ))

        assert response.status_code == HTTPStatus.OK
        # ensure only confirmed relationships are returned
        assert len(response.json()['caregivers']) == 2
        assert response.json() == {
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'institution': {
                'acronym_en': institution.acronym_en,
                'acronym_fr': institution.acronym_fr,
            },
            'data_access': 'ALL',
            'caregivers': [
                {
                    'language': user1.language,
                    'username': user1.username,
                    'devices': [
                        {
                            'type': device1.type,
                            'push_token': device1.push_token,
                        },
                    ],
                },
                {
                    'language': user2.language,
                    'username': user2.username,
                    'devices': [
                        {
                            'type': device2.type,
                            'push_token': device2.push_token,
                        },
                    ],
                },
            ],
        }


class TestPatientView:
    """Class wrapper for patient view tests."""

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        user_with_permission: Callable[[str], User],
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:patients-legacy', kwargs={'legacy_id': 42})

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(user_with_permission('patients.view_patient'))
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_not_found(self, admin_api_client: APIClient) -> None:
        """Test that a 404 is returned if the patient does not exist."""
        response = admin_api_client.get(reverse('api:patients-legacy', kwargs={'legacy_id': 42}))

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_retrieve(self, admin_api_client: APIClient) -> None:
        """Test that patient data is returned."""
        legacy_id = 42
        patient = Patient(legacy_id=legacy_id)

        response = admin_api_client.get(reverse('api:patients-legacy', kwargs={'legacy_id': legacy_id}))

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data['legacy_id'] == legacy_id
        assert data['first_name'] == patient.first_name
        assert data['date_of_birth'] == patient.date_of_birth.isoformat()

    def test_update_superuser(self, api_client: APIClient, admin_user: User) -> None:
        """Test patient updates data access success with superuser."""
        api_client.force_login(user=admin_user)
        legacy_id = 1
        patient = Patient(legacy_id=legacy_id, data_access='NTK')
        response = api_client.put(
            reverse(
                'api:patients-legacy',
                kwargs={'legacy_id': 1},
            ),
            data={'data_access': 'ALL'},
        )

        patient.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert patient.data_access == 'ALL'

    @pytest.mark.parametrize('permission_name', ['change_patient'])
    def test_update_with_permission(self, api_client: APIClient, permission_user: User) -> None:
        """Test patient updates data access success with permission."""
        api_client.force_login(user=permission_user)
        legacy_id = 1
        patient = Patient(legacy_id=legacy_id, data_access='NTK')
        response = api_client.put(
            reverse(
                'api:patients-legacy',
                kwargs={'legacy_id': 1},
            ),
            data={'data_access': 'ALL'},
        )

        patient.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert patient.data_access == 'ALL'

    @pytest.mark.parametrize('permission_name', ['change_patient'])
    def test_update_other_data(self, api_client: APIClient, permission_user: User) -> None:
        """Test patient updates only updates data access even if extra data is supplied."""
        api_client.force_login(user=permission_user)
        legacy_id = 1
        patient = Patient(legacy_id=legacy_id, data_access='NTK')
        response = api_client.put(
            reverse(
                'api:patients-legacy',
                kwargs={'legacy_id': 1},
            ),
            data={'data_access': 'ALL', 'ramq': 'SIMM86101799', 'first_name': 'Marge'},
        )

        patient.refresh_from_db()

        assert response.status_code == HTTPStatus.OK
        assert patient.data_access == 'ALL'
        assert patient.ramq == ''
        assert patient.first_name == 'Marge'

    @pytest.mark.parametrize('permission_name', ['change_patient'])
    def test_update_with_empty_data_access(self, api_client: APIClient, permission_user: User) -> None:
        """Test patient updates data access success with permission."""
        api_client.force_login(user=permission_user)
        legacy_id = 1
        patient = Patient(legacy_id=legacy_id, data_access='NTK')
        response = api_client.put(
            reverse(
                'api:patients-legacy',
                kwargs={'legacy_id': 1},
            ),
            data={'data_access': ''},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert patient.data_access == 'NTK'
        assert str(response.data['data_access']) == '{0}'.format(
            "[ErrorDetail(string='\"\" is not a valid choice.', code='invalid_choice')]",
        )

    @pytest.mark.parametrize('permission_name', ['change_patient'])
    def test_update_without_data_access(self, api_client: APIClient, permission_user: User) -> None:
        """Test patient updates data access success with permission."""
        api_client.force_login(user=permission_user)
        legacy_id = 1
        patient = Patient(legacy_id=legacy_id, data_access='NTK')
        response = api_client.put(
            reverse(
                'api:patients-legacy',
                kwargs={'legacy_id': 1},
            ),
            data={},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        patient.refresh_from_db()
        assert patient.data_access == 'NTK'
        assert str(response.data['data_access']) == '{0}'.format(
            "[ErrorDetail(string='This field is required.', code='required')]",
        )


class TestPatientExistsView:
    """Test class tests the api patients/exists."""

    input_data_cases = {
        'valid': [{'site_code': 'RVH', 'mrn': '9999996'}, {'site_code': 'LAC', 'mrn': '0765324'}],
        'invalid_site': [{'site_code': 'XXX', 'mrn': '9999996'}],
        'patient_not_found': [{'site_code': 'RVH', 'mrn': '1111111'}],
        'multiple_patients': [{'site_code': 'RVH', 'mrn': '9999996'}, {'site_code': 'RVH', 'mrn': '9999993'}],
        'invalid_mrn': [{'site_code': 'RVH', 'mrn': '111111111111111111'}],
    }

    def test_unauthenticated_unauthorized(
        self,
        api_client: APIClient,
        user: User,
        interface_engine_user: User,
    ) -> None:
        """Test that unauthenticated and unauthorized users cannot access the API."""
        url = reverse('api:patient-exists')

        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

        api_client.force_login(user)
        response = api_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

        api_client.force_login(interface_engine_user)
        response = api_client.options(url)

        assert response.status_code == HTTPStatus.OK

    def test_patient_exists_success(self, api_client: APIClient, admin_user: User) -> None:
        """Test api patient exists success."""
        api_client.force_login(user=admin_user)
        self._create_patient_identifiers()
        response = api_client.post(
            reverse('api:patient-exists'),
            data=self.input_data_cases['valid'],
        )

        assert response.status_code == HTTPStatus.OK
        assert response.data['uuid']
        assert response.data['legacy_id']
        assert len(response.data) == 2

    def test_patient_exists_invalid_site(self, api_client: APIClient, admin_user: User) -> None:
        """Test api patient exists invalid site error."""
        api_client.force_login(user=admin_user)
        self._create_patient_identifiers()
        response = api_client.post(
            reverse('api:patient-exists'),
            data=self.input_data_cases['invalid_site'],
        )
        assert 'Provided "XXX" site acronym does not exist.' in response.data[0]['site_code']
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_patient_exists_patient_not_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test api patient exists patient_not_found error."""
        api_client.force_login(user=admin_user)
        self._create_patient_identifiers()
        response = api_client.post(
            reverse('api:patient-exists'),
            data=self.input_data_cases['patient_not_found'],
        )
        expected_error = '{0} {1}'.format(
            'Cannot find patient record with the provided MRNs and sites or',
            'multiple patients found.',
        )
        assert expected_error in response.data['detail']
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_patient_exists_multiple_patients_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test api patient exists multiple_patients_foundd error."""
        api_client.force_login(user=admin_user)
        self._create_patient_identifiers()
        response = api_client.post(
            reverse('api:patient-exists'),
            data=self.input_data_cases['multiple_patients'],
        )
        expected_error = '{0} {1}'.format(
            'Cannot find patient record with the provided MRNs and sites or',
            'multiple patients found.',
        )
        assert expected_error in response.data['detail']
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_patient_exists_invalid_mrn(self, api_client: APIClient, admin_user: User) -> None:
        """Test api patient exists invalid mrn error."""
        api_client.force_login(user=admin_user)
        self._create_patient_identifiers()
        response = api_client.post(
            reverse('api:patient-exists'),
            data=self.input_data_cases['invalid_mrn'],
        )
        assert 'Ensure this field has no more than 10 characters.' in response.data[0]['mrn']
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_patient_exists_not_authorized(self, api_client: APIClient) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        response = api_client.post(
            reverse('api:patient-exists'),
            data=self.input_data_cases['valid'],
        )
        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def _create_patient_identifiers(self) -> None:
        """Set up patients with required identifiers."""
        site = Site(acronym='RVH')
        Site(acronym='LAC')
        HospitalPatient(
            patient=Patient(),
            mrn='9999996',
            site=site,
        )
        HospitalPatient(
            patient=Patient(ramq='OTES12345678'),
            mrn='9999993',
            site=site,
        )


def test_relationship_types_list_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    listener_user: User,
) -> None:
    """Test that unauthenticated and unauthorized users cannot access the API."""
    url = reverse('api:relationship-types-list')
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(listener_user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.OK


def test_relationship_types_list(api_client: APIClient, listener_user: User) -> None:
    """Test the return of the relationship types list."""
    api_client.force_login(user=listener_user)

    relationship_type = RelationshipType()

    response = api_client.get(reverse('api:relationship-types-list'))

    assert response.status_code == HTTPStatus.OK

    assert response.json()[0] == {
        'name': relationship_type.name,
        'description': relationship_type.description,
    }
