from decimal import Decimal
from typing import Any, Union

from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_django.asserts import assertNumQueries
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from opal.patients.factories import Patient
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
    patient = Patient()
    data = _create_sample_data()

    response = user_api_client.post(
        reverse('api:patients-data-quantity-create', kwargs={'patient_id': patient.pk}),
        data=data,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert QuantitySample.objects.count() == 1
    sample = QuantitySample.objects.get(patient=patient)

    data.update({'value': Decimal('12.34')})
    assert model_to_dict(sample, exclude=('id', 'patient')) == data


def test_quantitysample_create_data_list(user_api_client: APIClient) -> None:
    """Ensure that the endpoint can create a list of new quantity sample instances at once."""
    patient = Patient()
    data = [
        _create_sample_data(),
        _create_sample_data(60, QuantitySampleType.HEART_RATE, SampleSourceType.CLINICIAN),
    ]

    response = user_api_client.post(
        reverse('api:patients-data-quantity-create', kwargs={'patient_id': patient.pk}),
        data=data,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert QuantitySample.objects.count() == 2
    assert QuantitySample.objects.get(type=QuantitySampleType.BODY_MASS).value == Decimal('12.34')
    assert QuantitySample.objects.get(type=QuantitySampleType.HEART_RATE).value == Decimal('60.00')


def test_quantitysample_create_single_num_queries(admin_user: User) -> None:
    """Ensure that creating a single sample by passing a list uses the expected number of queries."""
    patient = Patient()
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
        response = view(request, patient_id=patient.pk)

        assert response.status_code == status.HTTP_201_CREATED


def test_quantitysample_create_multiple_num_queries(admin_user: User) -> None:
    """Ensure that creating multiple samples does not cause an explosion in queries executed."""
    patient = Patient()
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
        response = view(request, patient_id=patient.pk)

        assert response.status_code == status.HTTP_201_CREATED


def test_quantitysample_create_no_patient(user_api_client: APIClient) -> None:
    """Ensure a non-existent patient raises a 404."""
    response = user_api_client.post(reverse('api:patients-data-quantity-create', kwargs={'patient_id': 1}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.xfail(condition=True, reason='list currently not supported', strict=True)
def test_quantitysample_list_no_patient(user_api_client: APIClient) -> None:
    """Ensure a non-existent patient raises a 404."""
    response = user_api_client.get(reverse('api:patients-data-quantity-create', kwargs={'patient_id': 1}))

    assert response.status_code == status.HTTP_404_NOT_FOUND
