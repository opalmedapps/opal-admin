from http import HTTPStatus

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client
from django.urls import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertTemplateUsed

from opal.patients import factories
from opal.users.models import User

pytestmark = pytest.mark.django_db


def test_health_data_ui_template_used(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure the health data page can be rendered and patient info displayed."""
    user_client.force_login(admin_user)
    hd_patient = factories.Patient(ramq='OTES12345678')
    response = user_client.get(reverse('patients:health-data', kwargs={'id': hd_patient.id}))
    soup = BeautifulSoup(response.content, 'html.parser')
    patient_identifiers = soup.find_all('h4')

    assert response.status_code == HTTPStatus.OK
    assertTemplateUsed(response, 'patients/health-data/health_data_display.html')
    assert len(patient_identifiers) == 1
    assert hd_patient.first_name in str(patient_identifiers[0])
    assert hd_patient.last_name in str(patient_identifiers[0])
    assert hd_patient.ramq in str(patient_identifiers[0])


def test_health_data_ui_unauthorized_no_data(user_client: Client) -> None:
    """Ensure the no health data appears if user missing permission."""
    unauthorized_user = User.objects.create(username='marge_simpson')
    user_client.force_login(unauthorized_user)
    hd_patient = factories.Patient(ramq='OTES12345678')
    response = user_client.get(reverse('patients:health-data', kwargs={'id': hd_patient.id}))

    soup = BeautifulSoup(response.content, 'html.parser')
    patient_identifiers = soup.find_all('h4')

    assert response.status_code == HTTPStatus.OK
    assert not patient_identifiers


def test_health_data_ui_error_no_patient(user_client: Client, admin_user: AbstractUser) -> None:
    """Ensure an error is thrown if the requested patient health data doesnt exist."""
    user_client.force_login(admin_user)
    factories.Patient()
    with pytest.raises(ObjectDoesNotExist):
        user_client.get(reverse('patients:health-data', kwargs={'id': 42}))
