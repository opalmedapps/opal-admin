# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import Any
from uuid import uuid4

from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.asserts import assertContains, assertJSONEqual, assertNumQueries
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from opal.health_data import factories as health_data_factories
from opal.patients import factories as patient_factories
from opal.users.models import User

from ..api import views
from ..models import PatientReportedData, QuantitySample, QuantitySampleType, SampleSourceType

pytestmark = pytest.mark.django_db


def _create_sample_data(
    value: int | float | str = '12.34',
    sample_type: QuantitySampleType = QuantitySampleType.BODY_MASS,
    source: SampleSourceType = SampleSourceType.PATIENT,
) -> dict[str, Any]:
    return {
        'value': value,
        'type': sample_type.value,
        'start_date': timezone.now(),
        'source': source.value,
        'device': 'Awesome Smart Device (tm)',
    }


def test_quantitysample_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    listener_user: User,
) -> None:
    """Ensure that the API to create quantity samples requires an authenticated user."""
    patient = patient_factories.Patient.create()
    url = reverse('api:patients-data-quantity-create', kwargs={'uuid': patient.uuid})

    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(listener_user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.OK


def test_quantitysample_create_data_dict(admin_api_client: APIClient) -> None:
    """Ensure that the default create behaviour by passing a dictionary works."""
    patient = patient_factories.Patient.create()
    data = _create_sample_data()

    response = admin_api_client.post(
        reverse('api:patients-data-quantity-create', kwargs={'uuid': patient.uuid}),
        data=data,
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert QuantitySample.objects.count() == 1
    sample = QuantitySample.objects.get(patient=patient)

    data.update({'value': Decimal('12.34')})
    assert model_to_dict(sample, exclude=('id', 'patient', 'viewed_at', 'viewed_by')) == data


def test_quantitysample_create_data_list(admin_api_client: APIClient) -> None:
    """Ensure that the endpoint can create a list of new quantity sample instances at once."""
    patient = patient_factories.Patient.create()
    data = [
        _create_sample_data(),
        _create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN),
    ]

    response = admin_api_client.post(
        reverse('api:patients-data-quantity-create', kwargs={'uuid': patient.uuid}),
        data=data,
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert QuantitySample.objects.count() == 2
    assert QuantitySample.objects.get(type=QuantitySampleType.BODY_MASS).value == Decimal('12.34')
    assert QuantitySample.objects.get(type=QuantitySampleType.HEART_RATE).value == Decimal('60.00')


def test_quantitysample_create_single_num_queries(admin_user: User) -> None:
    """Ensure that creating a single sample by passing a list uses the expected number of queries."""
    patient = patient_factories.Patient.create()
    data = [_create_sample_data()]
    view = views.CreateQuantitySampleView.as_view()
    factory = APIRequestFactory()

    request = factory.post(
        '/unused',
        data,
    )
    force_authenticate(request, user=admin_user)

    # when passing a dictionary instead of a list (i.e., the default DRF create behaviour is used)
    # the number of queries is much higher (7) due to extra savepoints
    with assertNumQueries(2):
        response = view(request, uuid=patient.uuid)

        assert response.status_code == status.HTTP_201_CREATED


def test_quantitysample_create_multiple_num_queries(admin_user: User) -> None:
    """Ensure that creating multiple samples does not cause an explosion in queries executed."""
    patient = patient_factories.Patient.create()
    data = [
        _create_sample_data(),
        _create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN),
        _create_sample_data(source=SampleSourceType.CLINICIAN),
        _create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN),
    ]
    view = views.CreateQuantitySampleView.as_view()
    factory = APIRequestFactory()

    request = factory.post(
        '/unused',
        data,
    )
    force_authenticate(request, user=admin_user)

    with assertNumQueries(2):
        response = view(request, uuid=patient.uuid)

        assert response.status_code == status.HTTP_201_CREATED


def test_quantitysample_create_no_patient(admin_api_client: APIClient) -> None:
    """Ensure a non-existent patient raises a 404."""
    response = admin_api_client.post(reverse('api:patients-data-quantity-create', kwargs={'uuid': uuid4()}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.xfail(condition=True, reason='list currently not supported', strict=True)
def test_quantitysample_list_no_patient(admin_api_client: APIClient) -> None:
    """Ensure a non-existent patient raises a 404."""
    response = admin_api_client.get(reverse('api:patients-data-quantity-create', kwargs={'uuid': uuid4()}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_viewed_health_data_update_unauthenticated_unauthorized(api_client: APIClient, user: User) -> None:
    """Ensure `patient-viewed-health-data-update` endpoint returns 403 error for unauthorized user."""
    url = reverse('api:patient-viewed-health-data-update', kwargs={'uuid': uuid4()})

    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.patch(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'


def test_viewed_health_data_update_not_found_error(api_client: APIClient, orms_user: User) -> None:
    """Ensure `patient-viewed-health-data-update` endpoint returns 404 not found error for non-existing patient."""
    api_client.force_login(orms_user)

    response = api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': uuid4()}),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_viewed_health_data_update_with_no_quantities(api_client: APIClient, orms_user: User) -> None:
    """Ensure that the `patient-viewed-health-data-update` endpoint does not fail if patient has no quantities."""
    patient = patient_factories.Patient.create()
    api_client.force_login(orms_user)

    response = api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': patient.uuid}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert QuantitySample.objects.count() == 0


def test_viewed_health_data_update_for_specific_patient(api_client: APIClient, orms_user: User) -> None:
    """Ensure that the `/health-data/viewed/` endpoint updates quantities that belong to a specific patient."""
    api_client.force_login(orms_user)
    marge_patient = patient_factories.Patient.create(legacy_id=51, ramq='9999996')
    homer_patient = patient_factories.Patient.create(legacy_id=52, ramq='9999997')

    health_data_factories.QuantitySample.create(patient=marge_patient)
    health_data_factories.QuantitySample.create(patient=marge_patient)
    health_data_factories.QuantitySample.create(patient=homer_patient)

    response = api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': marge_patient.uuid}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert QuantitySample.objects.count() == 3
    assert (
        QuantitySample.objects.exclude(
            viewed_at=None,
            viewed_by='',
        ).count()
        == 2
    )

    client_user_id = api_client.session.get('_auth_user_id', '')
    user = User.objects.get(id=client_user_id)
    assert (
        QuantitySample.objects.exclude(
            viewed_at=None,
            viewed_by='',
        )[0].viewed_by
        == user.username
    )
    assert QuantitySample.objects.exclude(
        viewed_at=None,
        viewed_by='',
    )[0].viewed_at


def test_viewed_health_data_mark_only_new_records(api_client: APIClient, orms_user: User) -> None:
    """Ensure that the `/health-data/viewed/` endpoint marks as viewed only new quantity records (not old ones)."""
    api_client.force_login(orms_user)
    marge_patient = patient_factories.Patient.create(legacy_id=51, ramq='9999996')

    current_time = timezone.now()
    previous_day_time = current_time - timedelta(days=1)
    health_data_factories.QuantitySample.create(patient=marge_patient)
    health_data_factories.QuantitySample.create(patient=marge_patient)
    health_data_factories.QuantitySample.create(
        patient=marge_patient,
        viewed_at=previous_day_time,
        viewed_by='previous_day_user',
    )

    response = api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': marge_patient.uuid}),
    )

    assert response.status_code == status.HTTP_200_OK

    client_user_id = api_client.session.get('_auth_user_id', '')
    user = User.objects.get(id=client_user_id)

    # Ensure the existing viewed record was not changed
    assert (
        QuantitySample.objects.filter(
            viewed_at=previous_day_time,
            viewed_by='previous_day_user',
        ).count()
        == 1
    )

    assert (
        QuantitySample.objects.filter(
            viewed_by=user.username,
        ).count()
        == 2
    )


def test_unviewed_health_data_unauthorized(api_client: APIClient) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns 403 error for unauthorized user."""
    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unviewed_health_data_dict_error(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns an error when dictionary is passed."""
    api_client.force_login(orms_user)
    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data={'patient_uuid': 'test'},
    )

    assertContains(
        response=response,
        text=r'Expected a list of items but got type \"dict\".',
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def test_unviewed_health_data_empty_list(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns an error when empty list is passed."""
    api_client.force_login(orms_user)
    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data=[],
    )

    assertContains(
        response=response,
        text='This list may not be empty.',
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def test_unviewed_health_data_missing_field(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns an error when the field is missing."""
    api_client.force_login(orms_user)
    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data=[{'test': 'test'}],
    )

    assertContains(
        response=response,
        text='This field is required.',
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def test_unviewed_health_data_invalid_uuid(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns an error for invalid UUID value."""
    api_client.force_login(orms_user)
    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data=[{'patient_uuid': 'test'}],
    )

    assertContains(
        response=response,
        text='Must be a valid UUID.',
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def test_unviewed_health_data_non_existing_uuid(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns an error if patient's UUID does not exist."""
    api_client.force_login(orms_user)
    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data=[{'patient_uuid': '52f51e13-927d-4362-8258-8cc48233d226'}],
    )

    assertContains(
        response=response,
        text='[]',
        status_code=status.HTTP_200_OK,
    )


def test_unviewed_health_data_success(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns unviewed health data counts."""
    api_client.force_login(orms_user)
    marge_patient = patient_factories.Patient.create(legacy_id=1, ramq='TEST1234567')
    homer_patient = patient_factories.Patient.create(first_name='Homer', legacy_id=2, ramq='TEST7654321')
    health_data_factories.QuantitySample.create(patient=marge_patient, **(_create_sample_data()))
    health_data_factories.QuantitySample.create(
        patient=marge_patient,
        **(_create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN)),
    )
    health_data_factories.QuantitySample.create(
        patient=marge_patient,
        **(_create_sample_data(source=SampleSourceType.CLINICIAN)),
    )
    health_data_factories.QuantitySample.create(
        patient=homer_patient,
        **(_create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN)),
    )

    # Viewed quantity sample
    health_data_factories.QuantitySample.create(
        patient=homer_patient,
        **(_create_sample_data(70, QuantitySampleType.HEART_RATE, SampleSourceType.PATIENT)),
        viewed_at=timezone.now(),
        viewed_by='test_user',
    )

    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data=[
            {'patient_uuid': str(marge_patient.uuid)},
            {'patient_uuid': str(homer_patient.uuid)},
        ],
    )

    assert QuantitySample.objects.count() == 5

    assertJSONEqual(
        raw=response.content,
        expected_data=[
            {'count': 3, 'patient_uuid': f'{marge_patient.uuid}'},
            {'count': 1, 'patient_uuid': f'{homer_patient.uuid}'},
        ],
    )


def test_unviewed_health_data_success_no_unviewed(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint returns empty list when there's no unviewed health data."""
    api_client.force_login(orms_user)
    patient = patient_factories.Patient.create()
    client_user_id = api_client.session.get('_auth_user_id', '')
    user = User.objects.get(id=client_user_id)

    health_data_factories.QuantitySample.create(
        patient=patient,
        viewed_at=timezone.now(),
        viewed_by=user.username,
        **(_create_sample_data()),
    )
    health_data_factories.QuantitySample.create(
        patient=patient,
        viewed_at=timezone.now(),
        viewed_by=user.username,
        **(_create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN)),
    )
    health_data_factories.QuantitySample.create(
        patient=patient,
        viewed_at=timezone.now(),
        viewed_by=user.username,
        **(_create_sample_data(source=SampleSourceType.CLINICIAN)),
    )
    health_data_factories.QuantitySample.create(
        patient=patient,
        viewed_at=timezone.now(),
        viewed_by=user.username,
        **(_create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN)),
    )

    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data=[{'patient_uuid': str(patient.uuid)}],
    )

    assertContains(
        response=response,
        text='[]',
    )


def test_unviewed_health_data_no_duplicates(api_client: APIClient, orms_user: User) -> None:
    """Ensure `unviewed-health-data-patient-list` endpoint does not return duplicated UUIDs."""
    api_client.force_login(orms_user)
    patient = patient_factories.Patient.create()
    health_data_factories.QuantitySample.create(patient=patient, **(_create_sample_data()))
    health_data_factories.QuantitySample.create(
        patient=patient,
        **(_create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN)),
    )
    health_data_factories.QuantitySample.create(
        patient=patient,
        **(_create_sample_data(source=SampleSourceType.CLINICIAN)),
    )

    response = api_client.post(
        reverse('api:unviewed-health-data-patient-list'),
        data=[
            {'patient_uuid': str(patient.uuid)},
            {'patient_uuid': str(patient.uuid)},
        ],
    )

    assert QuantitySample.objects.count() == 3

    assertJSONEqual(
        raw=response.content,
        expected_data=[{'count': 3, 'patient_uuid': f'{patient.uuid}'}],
    )


def test_patientreporteddata_unauthenticated_unauthorized(
    api_client: APIClient,
    user: User,
    listener_user: User,
) -> None:
    """Ensure that the API to create/update patient-reported data requires an authenticated user."""
    patient = patient_factories.Patient.create()
    url = reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid})

    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthenticated request should fail'

    api_client.force_login(user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, 'unauthorized request should fail'

    api_client.force_login(listener_user)
    response = api_client.options(url)

    assert response.status_code == HTTPStatus.OK
    assert 'GET, PUT, PATCH' in response.headers['Allow']


def test_patientreporteddata_get_not_found(admin_api_client: APIClient) -> None:
    """A 404 is returned when no `PatientReportedData` exists for the patient."""
    response = admin_api_client.get(
        reverse('api:patients-data-reported', kwargs={'uuid': uuid4()}),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert PatientReportedData.objects.count() == 0


def test_patientreporteddata_get(admin_api_client: APIClient) -> None:
    """Existing `PatientReportedData` is returned for the patient."""
    patient = patient_factories.Patient.create()
    social_history = [{'foo': 'bar'}, {'bar': 'foo'}]
    PatientReportedData.objects.create(patient=patient, social_history=social_history)

    response = admin_api_client.get(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'social_history': social_history}


def test_patientreporteddata_post(admin_api_client: APIClient) -> None:
    """A 405 is returned when attempting to POST to the endpoint."""
    response = admin_api_client.post(
        reverse('api:patients-data-reported', kwargs={'uuid': uuid4()}),
        data={},
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_patientreporteddata_put_no_none(admin_api_client: APIClient) -> None:
    """Social history can not be None."""
    patient = patient_factories.Patient.create()

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': None},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert PatientReportedData.objects.count() == 0
    assert 'social_history' in response.json()


def test_patientreporteddata_put_create(admin_api_client: APIClient) -> None:
    """PUT creates a new `PatientReportedData` for the patient."""
    patient = patient_factories.Patient.create()

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': []},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert PatientReportedData.objects.count() == 1
    data = PatientReportedData.objects.get(patient=patient)
    assert data.social_history == []


def test_patientreporteddata_put_create_deceased_patient(admin_api_client: APIClient) -> None:
    """PUT cannot create `PatientReportedData` for a deceased patient."""
    patient = patient_factories.Patient.create(date_of_death=timezone.now())

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': []},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert PatientReportedData.objects.count() == 0


def test_patientreporteddata_put_update(admin_api_client: APIClient) -> None:
    """PUT updates an existing `PatientReportedData` for the patient."""
    patient = patient_factories.Patient.create()
    PatientReportedData.objects.create(patient=patient, social_history=[{'foo': 'bar'}])

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': []},
    )

    assert response.status_code == status.HTTP_200_OK
    assert PatientReportedData.objects.count() == 1
    data = PatientReportedData.objects.get(patient=patient)
    assert data.social_history == []


def test_patientreporteddata_put_update_deceased_patient(admin_api_client: APIClient) -> None:
    """PUT cannot update `PatientReportedData` for a deceased patient."""
    patient = patient_factories.Patient.create()
    data = PatientReportedData.objects.create(patient=patient, social_history=[{'foo': 'bar'}])
    patient.date_of_death = timezone.now()
    patient.save(update_fields=['date_of_death'])

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': []},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert PatientReportedData.objects.count() == 1
    data.refresh_from_db()
    assert data.social_history == [{'foo': 'bar'}]


def test_patientreporteddata_patch_update(admin_api_client: APIClient) -> None:
    """PATCH updates an existing `PatientReportedData` for the patient."""
    patient = patient_factories.Patient.create()
    PatientReportedData.objects.create(patient=patient, social_history=[{'foo': 'bar'}])

    response = admin_api_client.patch(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': []},
    )

    assert response.status_code == status.HTTP_200_OK
    assert PatientReportedData.objects.count() == 1
    data = PatientReportedData.objects.get(patient=patient)
    assert data.social_history == []


def test_patientreporteddata_patch_missing_returns_404(admin_api_client: APIClient) -> None:
    """PATCH returns 404 when `PatientReportedData` does not exist for the patient."""
    patient = patient_factories.Patient.create()

    response = admin_api_client.patch(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': []},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert PatientReportedData.objects.count() == 0


def test_patientreporteddata_patch_update_deceased_patient(admin_api_client: APIClient) -> None:
    """PATCH cannot update `PatientReportedData` for a deceased patient."""
    patient = patient_factories.Patient.create()
    data = PatientReportedData.objects.create(patient=patient, social_history=[{'foo': 'bar'}])
    patient.date_of_death = timezone.now()
    patient.save(update_fields=['date_of_death'])

    response = admin_api_client.patch(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': []},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert PatientReportedData.objects.count() == 1
    data.refresh_from_db()
    assert data.social_history == [{'foo': 'bar'}]


def test_patientreporteddata_elements_validated(admin_api_client: APIClient) -> None:
    """Elements in social history are validated."""
    patient = patient_factories.Patient.create()

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={'social_history': [None, {'foo': 'baz'}]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert PatientReportedData.objects.count() == 0
    errors = response.json()
    assert 'social_history' in errors
    assert len(errors['social_history']) == 2
    assert errors['social_history']['0'] == ['This field may not be null.']

    for item_error in errors['social_history']['1']:
        assert {'loc', 'msg', 'type'} == set(item_error.keys())


def test_patientreporteddata_no_subject_in_observation(admin_api_client: APIClient) -> None:
    """An observation with a subject is rejected."""
    patient = patient_factories.Patient.create()

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={
            'social_history': [
                {
                    'resourceType': 'Observation',
                    'id': '9ffd3fbb-7a1d-4abc-9c98-710673e99cca',
                    'meta': {'versionId': '1', 'lastUpdated': '2026-02-20T13:00:00-05:00'},
                    'status': 'preliminary',
                    'category': [
                        {
                            'coding': [
                                {
                                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                                    'code': 'social-history',
                                    'display': 'Social History',
                                }
                            ]
                        }
                    ],
                    'code': {
                        'coding': [
                            {'system': 'http://loinc.org', 'code': '74013-4', 'display': 'Alcoholic drinks per day'}
                        ]
                    },
                    'subject': {'reference': 'Patient/3a9a1eae-efb7-11ef-9c0b-fa163e7f8dbb', 'type': 'Patient'},
                    'effectiveDateTime': '2026-02-20T13:00:00-05:00',
                    'valueQuantity': {
                        'value': 2,
                        'unit': 'per day',
                        'system': 'http://unitsofmeasure.org',
                        'code': '/d',
                    },
                }
            ]
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert PatientReportedData.objects.count() == 0
    errors = response.json()
    assert len(errors['social_history']) == 1, errors
    assert errors['social_history']['0'] == [
        {
            'loc': ['subject'],
            'msg': 'subject cannot be set manually, it is assigned automatically when building the patient summary',
            'type': 'subject_forbidden',
        }
    ]


def test_patientreporteddata_valid_observation(admin_api_client: APIClient) -> None:
    """Valid observation data is accepted."""
    patient = patient_factories.Patient.create()

    response = admin_api_client.put(
        reverse('api:patients-data-reported', kwargs={'uuid': patient.uuid}),
        data={
            'social_history': [
                {
                    'resourceType': 'Observation',
                    'id': '9ffd3fbb-7a1d-4abc-9c98-710673e99cca',
                    'meta': {'versionId': '1', 'lastUpdated': '2026-02-20T13:00:00-05:00'},
                    'status': 'preliminary',
                    'category': [
                        {
                            'coding': [
                                {
                                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                                    'code': 'social-history',
                                    'display': 'Social History',
                                }
                            ]
                        }
                    ],
                    'code': {
                        'coding': [
                            {'system': 'http://loinc.org', 'code': '74013-4', 'display': 'Alcoholic drinks per day'}
                        ]
                    },
                    'effectiveDateTime': '2026-02-20T13:00:00-05:00',
                    'valueQuantity': {
                        'value': 2,
                        'unit': 'per day',
                        'system': 'http://unitsofmeasure.org',
                        'code': '/d',
                    },
                },
                {
                    'resourceType': 'Observation',
                    'id': '4786f60b-2f7f-4658-a5d5-d68363a1b3d9',
                    'meta': {'versionId': '1', 'lastUpdated': '2026-02-20T13:00:00-05:00'},
                    'status': 'preliminary',
                    'category': [
                        {
                            'coding': [
                                {
                                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                                    'code': 'social-history',
                                    'display': 'Social History',
                                }
                            ]
                        }
                    ],
                    'code': {
                        'coding': [
                            {'system': 'http://loinc.org', 'code': '72166-2', 'display': 'Tobacco smoking status'}
                        ]
                    },
                    'effectiveDateTime': '2026-02-20T13:00:00-05:00',
                    'valueCodeableConcept': {
                        'coding': [{'system': 'http://snomed.info/sct', 'code': '8392000', 'display': 'Non-smoker'}]
                    },
                },
            ]
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert PatientReportedData.objects.count() == 1
    data = PatientReportedData.objects.get(patient=patient)
    assert len(data.social_history) == 2, data.social_history
