# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import base64
from http import HTTPStatus

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

import pytest
from fpdf import FPDFException
from pytest_django.asserts import assertRaisesMessage
from pytest_mock.plugin import MockerFixture
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from opal.hospital_settings import factories as hospital_settings_factories
from opal.patients import factories as patient_factories
from opal.services.integration.hospital import NonOKResponseError
from opal.services.integration.tests.test_hospital import _MockResponse
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestQuestionnairesReportView:
    """Class wrapper for the `QuestionnairesReportView` tests."""

    def make_request(
        self,
        api_client: APIClient,
        admin_user: User,
        site: str,
        mrn: str,
    ) -> Response:
        """
        Make a request to the API view being tested (QuestionnairesReportView).

        Returns:
            The response of the API call.
        """
        api_client.force_authenticate(user=admin_user)

        url = reverse('api:questionnaires-reviewed')
        return api_client.post(url, data={'mrn': mrn, 'site': site})

    def test_unauthenticated_unauthorized(self, api_client: APIClient, user: User, orms_user: User) -> None:
        """Test the request while unauthenticated."""
        url = reverse('api:questionnaires-reviewed')
        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Authentication' in str(response.data['detail'])

        api_client.force_login(user)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

        api_client.force_login(orms_user)

        response = api_client.post(url)

        # input validation failed
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_mrn_length(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an MRN that has more than 10 characters."""
        hospital_patient = patient_factories.HospitalPatient.create()

        response = self.make_request(api_client, admin_user, hospital_patient.site.acronym, 'invalid mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['mrn'])

    def test_no_mrn(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty MRN."""
        hospital_patient = patient_factories.HospitalPatient.create()

        response = self.make_request(api_client, admin_user, hospital_patient.site.acronym, '')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['mrn'])

    def test_invalid_site_length(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a site code that has more than 10 characters."""
        hospital_patient = patient_factories.HospitalPatient.create()

        response = self.make_request(
            api_client,
            admin_user,
            get_random_string(length=11),
            hospital_patient.mrn,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['site'])

    def test_no_site(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty site acronym."""
        hospital_patient = patient_factories.HospitalPatient.create()

        response = self.make_request(api_client, admin_user, '', hospital_patient.mrn)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['site'])

    def test_invalid_site_mrn_length(self, api_client: APIClient, admin_user: User) -> None:
        """
        Test providing an MRN that has more than 10 characters.

        And a site acronym that has more than 10 characters.
        """
        response = self.make_request(api_client, admin_user, get_random_string(length=11), 'invalid mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['site'])
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['mrn'])

    def test_site_mrn_not_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a site acronym and an MRN that do not exist."""
        patient_factories.HospitalPatient.create()

        response = self.make_request(api_client, admin_user, 'wrong site', 'wrong mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Could not find `Patient` record with the provided MRN and site acronym.' in str(response.data)

    def test_no_site_mrn(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty site acronym and MRN."""
        response = self.make_request(api_client, admin_user, '', '')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['site'])
        assert 'This field may not be blank.' in str(response.data['mrn'])

    def test_report_generation_raises_does_not_exist_exception(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Ensure that report generation raises exception in case `Patient` record cannot be found."""
        message = 'Could not find `Patient` record with the provided MRN and site acronym.'
        error_response = {'detail': message}

        response = self.make_request(api_client, admin_user, 'TEST_SITE', 'TEST_MRN')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == error_response
        assertRaisesMessage(ObjectDoesNotExist, message)

    def test_report_generation_raises_multiple_object_exception(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Ensure that report generation raises exception if we get several patients with the same mrn/site acronyms."""
        message = 'Could not find `Patient` record with the provided MRN and site acronym.'
        error_response = {'detail': message}

        mocker.patch(
            'opal.patients.models.Patient.objects.get_patient_by_site_mrn_list',
            side_effect=MultipleObjectsReturned,
        )

        response = self.make_request(api_client, admin_user, 'TEST_SITE', 'TEST_MRN')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == error_response
        assertRaisesMessage(MultipleObjectsReturned, message)

    @pytest.mark.django_db(databases=['default', 'questionnaire'])
    def test_report_generation_error(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
        questionnaire_data: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Ensure that unsuccessful report generation is handled properly and does not cause any exceptions."""
        hospital_settings_factories.Institution.create(pk=1)
        patient = patient_factories.Patient.create(legacy_id=51)
        hospital_patient = patient_factories.HospitalPatient.create(
            patient=patient,
            site=patient_factories.Site.create(acronym='RVH'),
        )

        message = 'An error occurred during questionnaire report generation.'
        error_response = {'detail': message}

        mock_generate = mocker.patch(
            'opal.services.reports.questionnaire.generate_pdf',
            side_effect=FPDFException('some PDF error'),
        )

        response = self.make_request(api_client, admin_user, hospital_patient.site.acronym, hospital_patient.mrn)

        mock_generate.assert_called_once()
        assert caplog.records[1].message == 'An error occurred during questionnaire report generation'
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data == error_response

    @pytest.mark.django_db(databases=['default', 'questionnaire'])
    def test_report_export_error(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
        questionnaire_data: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Ensure that unsuccessful PDF report exporting is handled properly and does not cause any exceptions."""
        hospital_settings_factories.Institution.create(pk=1)
        patient = patient_factories.Patient.create(legacy_id=51)
        hospital_patient = patient_factories.HospitalPatient.create(
            patient=patient,
            site=patient_factories.Site.create(acronym='RVH'),
        )

        message = 'An error occurred while exporting a PDF report to the source system'
        error_response = {'detail': message}

        # mock an actual call to the legacy report generation service to raise a request error
        mock_generate = mocker.patch(
            'opal.services.reports.questionnaire.generate_pdf',
            return_value=b'pdf',
        )

        error_data = {
            'status': HTTPStatus.BAD_REQUEST.value,
            'message': 'some error',
        }

        mock_export_pdf_report = mocker.patch(
            'opal.services.integration.hospital.add_questionnaire_report',
            side_effect=NonOKResponseError(_MockResponse(HTTPStatus.BAD_REQUEST, error_data)),
        )

        document_date = timezone.now().replace(microsecond=0)
        mocker.patch(
            'django.utils.timezone.now',
            return_value=document_date,
        )

        response = self.make_request(api_client, admin_user, hospital_patient.site.acronym, hospital_patient.mrn)

        mock_export_pdf_report.assert_called_once()
        mock_generate.assert_called_once()
        assert caplog.records[1].message == message
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data == error_response

    @pytest.mark.django_db(databases=['default', 'questionnaire'])
    def test_post_report_export(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
        questionnaire_data: None,
    ) -> None:
        """Test PDF report export request sent to the source system."""
        hospital_settings_factories.Institution.create(pk=1)
        patient = patient_factories.Patient.create(legacy_id=51)
        hospital_patient = patient_factories.HospitalPatient.create(
            patient=patient,
            site=patient_factories.Site.create(acronym='RVH'),
        )

        # mock an actual call to the legacy report generation service to raise a request error
        mocker.patch(
            'opal.services.reports.questionnaire.generate_pdf',
            return_value=b'pdf',
        )

        mock_export_pdf_report = mocker.patch(
            'opal.services.integration.hospital.add_questionnaire_report',
        )

        document_date = timezone.now().replace(microsecond=0)
        mocker.patch(
            'django.utils.timezone.now',
            return_value=document_date,
        )

        response = self.make_request(api_client, admin_user, hospital_patient.site.acronym, hospital_patient.mrn)

        mock_export_pdf_report.assert_called_once_with(
            hospital_patient.mrn,
            hospital_patient.site.acronym,
            base64.b64encode(b'pdf'),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    # Marking this slow since the test uses chromium
    @pytest.mark.slow
    # Allow hosts to make the test work for Windows, Linux and Unix-based environements
    @pytest.mark.allow_hosts(['127.0.0.1'])
    @pytest.mark.django_db(databases=['default', 'questionnaire'])
    def test_pdf_generation(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
        questionnaire_data: None,
    ) -> None:
        """Test that PDF report is created successfully."""
        hospital_settings_factories.Institution.create(pk=1)
        patient = patient_factories.Patient.create(legacy_id=51)
        hospital_patient = patient_factories.HospitalPatient.create(
            patient=patient,
            site=patient_factories.Site.create(acronym='RVH'),
        )

        mock_export_pdf_report = mocker.patch(
            'opal.services.hospital.hospital.SourceSystemService.export_pdf_report',
            return_value={'status': 'success'},
        )

        response = self.make_request(api_client, admin_user, hospital_patient.site.acronym, hospital_patient.mrn)

        assert response.status_code == status.HTTP_200_OK
        assert response.data is None
        calls = mock_export_pdf_report.call_args_list

        assert len(calls) == 1
        encoded_pdf = calls[0].args[0].base64_content

        assert encoded_pdf
        base64_pdf = base64.b64decode(encoded_pdf)

        assert base64_pdf.startswith(b'%PDF-')
