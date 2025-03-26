"""Test module for the `patients` app REST API endpoints."""

import copy
import json
from datetime import datetime
from http import HTTPStatus
from typing import Any

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual, assertRaisesMessage
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient

from opal.caregivers import models as caregiver_models
from opal.caregivers.factories import CaregiverProfile, Device, RegistrationCode
from opal.hospital_settings.factories import Institution, Site
from opal.patients import models as patient_models
from opal.patients.factories import HospitalPatient, Patient, Relationship
from opal.users import factories as caregiver_factories
from opal.users.models import Caregiver, User

pytestmark = pytest.mark.django_db(databases=['default'])


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
        status='CON',
        # Pytest insists on fetching the SELF role type instance using a queryset for some reason, factory doesn't work
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
    }
    assert response.json()[1] == {
        'caregiver_id': caregiver2.user.id,
        'first_name': caregiver2.user.first_name,
        'last_name': caregiver2.user.last_name,
        'status': relationship2.status,
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


class TestApiRetrieveRegistrationDetails:
    """A class to test RetrieveRegistrationDetails apis."""

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

    def test_registration_code_detailed(self, api_client: APIClient, admin_user: User) -> None:
        """Test api registration code with detailed serializer."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        caregiver = CaregiverProfile()
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)

        # Build relationships: hospital_patient -> site -> institution
        institution = Institution()
        site = Site(institution=institution)
        hospital_patient = HospitalPatient(patient=patient, site=site)

        response = api_client.get(
            '{0}{1}'.format(
                reverse(
                    'api:registration-code',
                    kwargs={'code': registration_code.code},
                ),
                '?detailed',
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            'caregiver': {
                'uuid': str(caregiver.uuid),
                'first_name': caregiver.user.first_name,
                'last_name': caregiver.user.last_name,
                'legacy_id': caregiver.legacy_id,
            },
            'patient': {
                'uuid': str(patient.uuid),
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'date_of_birth': datetime.strftime(patient.date_of_birth, '%Y-%m-%d'),
                'sex': patient.sex.value,
                'ramq': patient.ramq,
                'legacy_id': patient.legacy_id,
            },
            'hospital_patients': [
                {
                    'mrn': hospital_patient.mrn,
                    'site_code': site.code,
                },
            ],
            'relationship_type': {
                'name': relationship.type.name,
                'role_type': relationship.type.role_type.value,
            },
        }


class TestApiRegistrationCompletion:
    """Test class tests the api registration/<str: code>/register."""

    input_data = {
        'patient': {
            'legacy_id': 1,
        },
        'caregiver': {
            'language': 'fr',
            'phone_number': '+15141112222',
            'username': 'test-username',
            'legacy_id': 1,
        },
        'security_answers': [
            {
                'question': 'correct?',
                'answer': 'yes',
            },
            {
                'question': 'correct?',
                'answer': 'maybe',
            },
        ],
    }

    def test_register_success(self, api_client: APIClient, admin_user: User) -> None:
        """Test api registration register success."""
        api_client.force_login(user=admin_user)
        # Build relationships: code -> relationship -> patient
        patient = Patient()
        caregiver = CaregiverProfile()
        relationship = Relationship(patient=patient, caregiver=caregiver)
        registration_code = RegistrationCode(relationship=relationship)
        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
            format='json',
        )
        registration_code.refresh_from_db()
        security_answers = caregiver_models.SecurityAnswer.objects.all()
        assert response.status_code == HTTPStatus.OK
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED
        assert len(security_answers) == 2

    def test_existing_patient_caregiver(self, api_client: APIClient, admin_user: User) -> None:
        """Existing patient and caregiver don't cause the serializer to fail."""
        api_client.force_login(user=admin_user)
        Relationship(patient__legacy_id=1, caregiver__legacy_id=1)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': '123456'},
            ),
            data=self.input_data,
            format='json',
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_non_existent_registration_code(self, api_client: APIClient, admin_user: User) -> None:
        """Test non-existent registration code."""
        api_client.force_login(user=admin_user)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': 'code11111111'},
            ),
            data=self.input_data,
            format='json',
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_registered_registration_code(self, api_client: APIClient, admin_user: User) -> None:
        """Test registered registration code."""
        api_client.force_login(user=admin_user)
        registration_code = RegistrationCode(
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        )

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
            format='json',
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_register_with_invalid_input_data(self, api_client: APIClient, admin_user: User) -> None:
        """Test validation of patient's legacy_id."""
        api_client.force_login(user=admin_user)

        invalid_data: dict = copy.deepcopy(self.input_data)
        invalid_data['patient']['legacy_id'] = 0

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': '123456'},
            ),
            data=invalid_data,
            format='json',
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {
            'patient': {'legacy_id': ['Ensure this value is greater than or equal to 1.']},
        }

    def test_register_with_invalid_phone(self, api_client: APIClient, admin_user: User) -> None:
        """Test validation of the phone number."""
        api_client.force_login(user=admin_user)

        registration_code = RegistrationCode()

        invalid_data: dict = copy.deepcopy(self.input_data)
        invalid_data['caregiver']['phone_number'] = '1234567890'

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=invalid_data,
            format='json',
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {
            'detail': "({'phone_number': [ValidationError(['Enter a valid value.'])]}, None, None)",
        }
        # check that no data was changed
        registration_code.refresh_from_db()
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.NEW
        security_answers = caregiver_models.SecurityAnswer.objects.all()
        assert not security_answers

    def test_remove_skeleton_caregiver(self, api_client: APIClient, admin_user: User) -> None:
        """Test api registration register remove skeleton caregiver."""
        api_client.force_login(user=admin_user)
        # Build existing caregiver
        caregiver = caregiver_factories.Caregiver(
            username='test-username',
            first_name='caregiver',
            last_name='test',
        )
        caregiver_profile = CaregiverProfile(user=caregiver)
        # Build skeleton user
        skeleton = caregiver_factories.Caregiver(
            username='skeleton-username',
            first_name='skeleton',
            last_name='test',
        )
        skeleton_profile = CaregiverProfile(user=skeleton)
        # Build relationships: code -> relationship -> patient
        relationship = Relationship(caregiver=skeleton_profile)
        registration_code = RegistrationCode(relationship=relationship)

        response = api_client.post(
            reverse(
                'api:registration-register',
                kwargs={'code': registration_code.code},
            ),
            data=self.input_data,
            format='json',
        )

        registration_code.refresh_from_db()
        relationship.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED
        assert relationship.caregiver.id == caregiver_profile.id
        assert relationship.caregiver.user.id == caregiver.id
        assert not Caregiver.objects.filter(username=skeleton.username).exists()
        assert not caregiver_models.CaregiverProfile.objects.filter(user=skeleton).exists()


class TestPatientDemographicView:
    """Class wrapper for patient demographic endpoint tests."""

    def test_demographic_update_unauthorized(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthorized."""
        # Make a `PUT` request without proper permissions.
        response = api_client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

        # Make a `PATCH` request without proper permissions.
        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertContains(
            response=response,
            text='Authentication credentials were not provided.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_demographic_update_with_empty_mrns(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns an error if the MRNs list is empty."""
        client = self._get_client_with_permissions(api_client)
        data = self._get_valid_input_data()
        data['mrns'] = []

        response = client.put(
            reverse('api:patient-demographic-update'),
            data=data,
            format='json',
        )

        assertContains(
            response=response,
            text='This list may not be empty.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

        response = api_client.patch(
            reverse('api:patient-demographic-update'),
            data=data,
            format='json',
        )

        assertContains(
            response=response,
            text='This list may not be empty.',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_demographic_update_invalid_mrns(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns an error if the MRNs list dictionaries are invalid."""
        client = self._get_client_with_permissions(api_client)
        data = self._get_valid_input_data()
        data['mrns'] = [
            {'site': 'RVH', 'mrn_error': '9999996', 'is_active_erorr': True},
        ]

        response = client.put(
            reverse('api:patient-demographic-update'),
            data=data,
            format='json',
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

        response = client.patch(
            reverse('api:patient-demographic-update'),
            data=data,
            format='json',
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
    ) -> None:
        """Ensure the endpoint returns an error if provided sites do not exist."""
        client = self._get_client_with_permissions(api_client)

        response = client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=[
                {
                    'site_code': ['Provided "RVH" site code does not exist.'],
                },
                {
                    'site_code': ['Provided "MGH" site code does not exist.'],
                },
            ],
        )

        response = client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=[
                {
                    'site_code': ['Provided "RVH" site code does not exist.'],
                },
                {
                    'site_code': ['Provided "MGH" site code does not exist.'],
                },
            ],
        )

    def test_demographic_update_mrn_site_pairs_do_not_exist(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint raises a NotFound exception if provided MRN/site pairs do not exist."""
        Site(code='RVH')
        Site(code='MGH')

        client = self._get_client_with_permissions(api_client)

        response = client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertRaisesMessage(
            expected_exception=NotFound,
            expected_message='{0} {1}'.format(
                'Cannot find patient record with the provided MRNs and sites.',
                'Make sure that MRN/site pairs refer to the same patient.',
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
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
    ) -> None:
        """Ensure the endpoint raises a NotFound exception if MRNs referring to different patients."""
        patient_one = Patient()
        patient_two = Patient(ramq='TEST01161972')

        HospitalPatient(
            patient=patient_one,
            mrn='9999996',
            site=Site(code='RVH'),
        )
        HospitalPatient(
            patient=patient_two,
            mrn='9999997',
            site=Site(code='MGH'),
        )

        client = self._get_client_with_permissions(api_client)

        response = client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assertRaisesMessage(
            expected_exception=NotFound,
            expected_message='{0} {1}'.format(
                'Cannot find patient record with the provided MRNs and sites.',
                'Make sure that MRN/site pairs refer to the same patient.',
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
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
            site=Site(code='RVH'),
        )
        HospitalPatient(
            patient=patient,
            mrn='9999997',
            site=Site(code='MGH'),
        )

        client = self._get_client_with_permissions(api_client)
        response = client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

        response = client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

    def test_demographic_update_no_relationship(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint can update patient info when the patient does not have a self relationship (no user)."""
        rvh_site = Site(code='RVH')
        mgh_site = Site(code='MGH')
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

        client = self._get_client_with_permissions(api_client)
        response = client.put(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

        response = client.patch(
            reverse('api:patient-demographic-update'),
            data=self._get_valid_input_data(),
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK

        assertJSONEqual(
            raw=json.dumps(response.json()),
            expected_data=self._get_valid_input_data(),
        )

    def test_demographic_update_deceased_patient(
        self,
        api_client: APIClient,
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
            site=Site(code='RVH'),
        )
        HospitalPatient(
            patient=patient,
            mrn='9999997',
            site=Site(code='MGH'),
        )

        client = self._get_client_with_permissions(api_client)
        payload = self._get_valid_input_data()
        payload['date_of_death'] = datetime.now().replace(
            microsecond=0,
        ).astimezone().isoformat()

        response = client.put(
            reverse('api:patient-demographic-update'),
            data=payload,
            format='json',
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

    def _get_client_with_permissions(self, api_client: APIClient) -> APIClient:
        """
        Add permissions to a user and authorize it.

        Returns:
            Authorized API client.
        """
        user = caregiver_factories.Caregiver(username='lisaphillips')
        permission = Permission.objects.get(codename='change_patient')
        user.user_permissions.add(permission)
        api_client.force_login(user=user)
        return api_client


class TestPatientCaregiversView:
    """Class wrapper for patient caregivers endpoint tests."""

    def test_get_patient_caregivers_success(self, api_client: APIClient, admin_user: User) -> None:
        """Test get patient caregivers success."""
        api_client.force_login(user=admin_user)

        legacy_id = 1
        patient = Patient(legacy_id=legacy_id)

        user1 = caregiver_factories.Caregiver(language='en', phone_number='+11234567890')
        user2 = caregiver_factories.Caregiver(language='fr', phone_number='+11234567891')
        caregiver1 = CaregiverProfile(user=user1)
        caregiver2 = CaregiverProfile(user=user2)
        Relationship(caregiver=caregiver1, patient=patient)
        Relationship(caregiver=caregiver2, patient=patient)
        device1 = Device(caregiver=caregiver1)
        device2 = Device(caregiver=caregiver2)

        institution = Institution()
        response = api_client.get(reverse(
            'api:patient-caregivers',
            kwargs={'legacy_id': legacy_id},
        ))
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'institution_code': institution.code,
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
