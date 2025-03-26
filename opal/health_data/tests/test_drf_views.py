from decimal import Decimal
from typing import Any, Union
from uuid import uuid4

from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.asserts import assertNumQueries
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from opal.health_data import factories as health_data_factories
from opal.patients import factories as patient_factories
from opal.users.models import User

from ..api import views
from ..models import QuantitySample, QuantitySampleType, SampleSourceType

pytestmark = pytest.mark.django_db


def _create_sample_data(
    value: Union[int, float, str] = '12.34',
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


def test_quantitysample_create_data_dict(user_api_client: APIClient) -> None:
    """Ensure that the default create behaviour by passing a dictionary works."""
    patient = patient_factories.Patient()
    data = _create_sample_data()

    response = user_api_client.post(
        reverse('api:patients-data-quantity-create', kwargs={'uuid': patient.uuid}),
        data=data,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert QuantitySample.objects.count() == 1
    sample = QuantitySample.objects.get(patient=patient)

    data.update({'value': Decimal('12.34')})
    assert model_to_dict(sample, exclude=('id', 'patient', 'viewed_at', 'viewed_by')) == data


def test_quantitysample_create_data_list(user_api_client: APIClient) -> None:
    """Ensure that the endpoint can create a list of new quantity sample instances at once."""
    patient = patient_factories.Patient()
    data = [
        _create_sample_data(),
        _create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN),
    ]

    response = user_api_client.post(
        reverse('api:patients-data-quantity-create', kwargs={'uuid': patient.uuid}),
        data=data,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert QuantitySample.objects.count() == 2
    assert QuantitySample.objects.get(type=QuantitySampleType.BODY_MASS).value == Decimal('12.34')
    assert QuantitySample.objects.get(type=QuantitySampleType.HEART_RATE).value == Decimal('60.00')


def test_quantitysample_create_single_num_queries(admin_user: User) -> None:
    """Ensure that creating a single sample by passing a list uses the expected number of queries."""
    patient = patient_factories.Patient()
    data = [_create_sample_data()]
    view = views.CreateQuantitySampleView.as_view()
    factory = APIRequestFactory()

    request = factory.post(
        '/unused',
        data,
        format='json',
    )
    force_authenticate(request, user=admin_user)

    # when passing a dictionary instead of a list (i.e., the default DRF create behaviour is used)
    # the number of queries is much higher (7) due to extra savepoints
    with assertNumQueries(2):
        response = view(request, uuid=patient.uuid)

        assert response.status_code == status.HTTP_201_CREATED


def test_quantitysample_create_multiple_num_queries(admin_user: User) -> None:
    """Ensure that creating multiple samples does not cause an explosion in queries executed."""
    patient = patient_factories.Patient()
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
        format='json',
    )
    force_authenticate(request, user=admin_user)

    with assertNumQueries(2):
        response = view(request, uuid=patient.uuid)

        assert response.status_code == status.HTTP_201_CREATED


def test_quantitysample_create_no_patient(user_api_client: APIClient) -> None:
    """Ensure a non-existent patient raises a 404."""
    response = user_api_client.post(reverse('api:patients-data-quantity-create', kwargs={'uuid': uuid4()}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.xfail(condition=True, reason='list currently not supported', strict=True)
def test_quantitysample_list_no_patient(user_api_client: APIClient) -> None:
    """Ensure a non-existent patient raises a 404."""
    response = user_api_client.get(reverse('api:patients-data-quantity-create', kwargs={'uuid': uuid4()}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_viewed_health_data_update_unauthorized(api_client: APIClient) -> None:
    """Ensure `patient-viewed-health-data-update` endpoint returns 403 error for unauthorized user."""
    response = api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': uuid4()}),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_viewed_health_data_update_not_found_error(user_api_client: APIClient) -> None:
    """Ensure `patient-viewed-health-data-update` endpoint returns 404 not found error for non-existing patient."""
    response = user_api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': uuid4()}),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_viewed_health_data_update_with_no_quantities(user_api_client: APIClient) -> None:
    """Ensure that the `patient-viewed-health-data-update` endpoint does not fail if patient has no quantities."""
    patient = patient_factories.Patient()

    response = user_api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': patient.uuid}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert QuantitySample.objects.count() == 0


def test_viewed_health_data_update_for_specific_patient(user_api_client: APIClient) -> None:
    """Ensure that the `/health-data/viewed/` endpoint updates quantities that belong to a specific patient."""
    marge_patient = patient_factories.Patient(legacy_id=51, ramq='9999996')
    homer_patient = patient_factories.Patient(legacy_id=52, ramq='9999997')

    health_data_factories.QuantitySample(patient=marge_patient)
    health_data_factories.QuantitySample(patient=marge_patient)
    health_data_factories.QuantitySample(patient=homer_patient)

    response = user_api_client.patch(
        reverse('api:patient-viewed-health-data-update', kwargs={'uuid': marge_patient.uuid}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert QuantitySample.objects.count() == 3
    assert QuantitySample.objects.exclude(
        viewed_at__isnull=True,
        viewed_by__exact='',
    ).count() == 2

    client_user_id = user_api_client.session.get('_auth_user_id', '')
    user = User.objects.get(id=client_user_id)
    assert QuantitySample.objects.exclude(  # type: ignore [union-attr]
        viewed_at__isnull=True,
        viewed_by__exact='',
    ).first().viewed_by == user.username
    assert QuantitySample.objects.exclude(  # type: ignore [union-attr]
        viewed_at__isnull=True,
        viewed_by__exact='',
    ).first().viewed_at
