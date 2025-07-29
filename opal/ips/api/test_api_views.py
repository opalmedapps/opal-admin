# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test module for the REST API endpoints of the `ips` app."""

from pprint import pprint
from uuid import uuid4

from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIClient

from opal.ips.api.views import GetPatientSummary
from opal.patients import factories as patient_factories
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default'])

class TestGetPatientSummary:
    """Class wrapper for IPS endpoint tests."""

    def test_patient_summary_unauthenticated(
        self,
        api_client: APIClient,
    ) -> None:
        """Ensure the endpoint returns a 403 error if the user is unauthenticated."""
        response = api_client.get(reverse('api:patient-summary', kwargs={'uuid': uuid4()}))

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
        response = user_api_client.get(reverse('api:patient-summary', kwargs={'uuid': uuid4()}))

        assertContains(
            response=response,
            text='You do not have permission to perform this action.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # TODO update with real content
    def test_get_patient_summary_success(
        self,
        api_client: APIClient,
        listener_user: User,
    ) -> None:
        """Ensure the endpoint can retrieve a patient summary with no errors."""
        api_client.force_login(listener_user)

        uuid = uuid4()
        patient = patient_factories.Patient.create(uuid=uuid)

        response = api_client.get(reverse('api:patient-summary', kwargs={'uuid': uuid}))

        print(response)
        pprint(vars(response))

        assert 2 + 2 == 5
