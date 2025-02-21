# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from http import HTTPStatus
from uuid import uuid4

from django.test import Client
from django.urls import reverse

import pytest
from bs4 import BeautifulSoup
from pytest_django.asserts import assertTemplateUsed

from opal.patients import factories as patient_factories

from .. import factories as healthdata_factories
from ..models import QuantitySampleType

pytestmark = pytest.mark.django_db

MISSING_DATA_WARNINGS = (
    'No data found for Body Mass',
    'No data found for Body Temperature',
    'No data found for Heart Rate',
    'No data found for Heart Rate Variability',
    'No data found for Oxygen Saturation',
    'No data found for Blood Pressure',
)


def test_health_data_ui_template_used(admin_client: Client) -> None:
    """Ensure the health data page can be rendered and patient info displayed."""
    hd_patient = patient_factories.Patient.create(ramq='OTES12345678')

    response = admin_client.get(reverse('health_data:health-data-ui', kwargs={'uuid': hd_patient.uuid}))

    soup = BeautifulSoup(response.content, 'html.parser')
    patient_identifiers = soup.find_all('h4')

    assert response.status_code == HTTPStatus.OK
    assertTemplateUsed(response, 'chart_display.html')
    assert len(patient_identifiers) == 1
    assert hd_patient.first_name in str(patient_identifiers[0])
    assert hd_patient.last_name in str(patient_identifiers[0])
    assert hd_patient.ramq in str(patient_identifiers[0])


def test_health_data_ui_unauthorized_no_data(user_client: Client) -> None:
    """Ensure that no health data appears if user missing permission."""
    hd_patient = patient_factories.Patient.create(ramq='OTES12345678')

    response = user_client.get(reverse('health_data:health-data-ui', kwargs={'uuid': hd_patient.uuid}))

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_health_data_ui_error_no_patient(admin_client: Client) -> None:
    """Ensure an error is thrown if the requested patient health data doesnt exist."""
    response = admin_client.get(reverse('health_data:health-data-ui', kwargs={'uuid': uuid4()}))

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_health_data_template_plots_detected(admin_client: Client) -> None:
    """Ensure generate plotly content shows in template."""
    patient = patient_factories.Patient.create()
    healthdata_factories.QuantitySample.create(patient=patient, type=QuantitySampleType.BODY_MASS)
    healthdata_factories.QuantitySample.create(patient=patient, type=QuantitySampleType.BODY_TEMPERATURE)
    healthdata_factories.QuantitySample.create(patient=patient, type=QuantitySampleType.HEART_RATE)
    healthdata_factories.QuantitySample.create(patient=patient, type=QuantitySampleType.HEART_RATE_VARIABILITY)
    healthdata_factories.QuantitySample.create(patient=patient, type=QuantitySampleType.OXYGEN_SATURATION)
    healthdata_factories.QuantitySample.create(patient=patient, type=QuantitySampleType.BLOOD_PRESSURE_SYSTOLIC)
    healthdata_factories.QuantitySample.create(patient=patient, type=QuantitySampleType.BLOOD_PRESSURE_DIASTOLIC)

    response = admin_client.get(reverse('health_data:health-data-ui', kwargs={'uuid': patient.uuid}))

    soup = BeautifulSoup(response.content, 'html.parser')
    no_data_lines = soup.find_all('h5')
    for line in no_data_lines:
        if line.string:
            assert line.string not in MISSING_DATA_WARNINGS

    assert response.status_code == HTTPStatus.OK


def test_health_data_generate_plot_empty(admin_client: Client) -> None:
    """Ensure generate plot returns nothing given no QuantitySample data, and the correct info lines are shown."""
    patient = patient_factories.Patient.create()

    response = admin_client.get(reverse('health_data:health-data-ui', kwargs={'uuid': patient.uuid}))

    soup = BeautifulSoup(response.content, 'html.parser')
    no_data_lines = soup.find_all('h5')
    for line in no_data_lines:
        if line.string:
            assert line.string in MISSING_DATA_WARNINGS

    assert response.status_code == HTTPStatus.OK
