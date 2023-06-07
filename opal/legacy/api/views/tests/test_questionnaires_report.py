from pathlib import Path
from typing import Any

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

import pytest
from pytest_django.asserts import assertRaisesMessage
from pytest_django.fixtures import SettingsWrapper
from pytest_mock.plugin import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from opal.hospital_settings import factories as hospital_settings_factories
from opal.patients import factories as patient_factories
from opal.services.hospital.hospital import OIEReportExportData
from opal.services.reports import QuestionnaireReportRequestData
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
    ) -> Any:
        """
        Make a request to the API view being tested (QuestionnairesReportView).

        Returns:
            The response of the API call.
        """
        api_client.force_authenticate(user=admin_user)

        url = reverse('api:questionnaires-reviewed')
        return api_client.post(url, data={'mrn': mrn, 'site': site}, format='json')

    def test_unauthenticated(self, api_client: APIClient, admin_user: User) -> None:
        """Test the request while unauthenticated."""
        hospital_patient = patient_factories.HospitalPatient()

        url = reverse('api:questionnaires-reviewed')
        response = api_client.post(
            url,
            data={'mrn': '9999996', 'site': hospital_patient.site.code},
            format='json',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Authentication' in str(response.data['detail'])

    def test_invalid_mrn_length(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an MRN that has more than 10 characters."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, 'invalid mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['mrn'])

    def test_no_mrn(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty MRN."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, '')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['mrn'])

    def test_invalid_site_length(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a site code that has more than 10 characters."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(
            api_client,
            admin_user,
            get_random_string(length=11),
            hospital_patient.mrn,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['site'])

    def test_no_site(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty site code."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, '', hospital_patient.mrn)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['site'])

    def test_invalid_site_mrn_length(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an MRN that has more than 10 characters and a site code that has more than 10 characters."""
        response = self.make_request(api_client, admin_user, get_random_string(length=11), 'invalid mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['site'])
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['mrn'])

    def test_site_mrn_not_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a site code and an MRN that do not exist."""
        patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, 'wrong site', 'wrong mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Could not find `Patient` record with the provided MRN and site code.' in str(response.data)

    def test_no_site_mrn(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty site code and MRN."""
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
        message = 'Could not find `Patient` record with the provided MRN and site code.'
        error_response = {'status': 'error', 'message': message}

        # mock the logger
        mock_logger = mocker.patch('logging.Logger.error', return_value=None)

        response = self.make_request(api_client, admin_user, 'TEST_SITE', 'TEST_MRN')

        mock_logger.assert_called_once_with(message)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == error_response
        assertRaisesMessage(ObjectDoesNotExist, message)

    def test_report_generation_raises_multiple_object_exception(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Ensure that report generation raises exception if we get several patients with the same mrn/site codes."""
        message = 'Could not find `Patient` record with the provided MRN and site code.'
        error_response = {'status': 'error', 'message': message}

        # mock the logger
        mock_logger = mocker.patch('logging.Logger.error', return_value=None)

        # mock the get_patient_by_site_mrn_list
        mocker.patch(
            'opal.patients.models.Patient.objects.get_patient_by_site_mrn_list',
            side_effect=MultipleObjectsReturned,
        )

        response = self.make_request(api_client, admin_user, 'TEST_SITE', 'TEST_MRN')

        mock_logger.assert_called_once_with(message)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == error_response
        assertRaisesMessage(MultipleObjectsReturned, message)

    def test_unset_language(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure that unset language is handled properly and does not throw an exception."""
        settings.LANGUAGES = [('fr', 'French')]

        institution = hospital_settings_factories.Institution(pk=1)
        hospital_patient = patient_factories.HospitalPatient(
            site=patient_factories.Site(code='RVH'),
        )

        # mock an actual call to the legacy report generation service to raise a request error
        mock_generate_questionnaire_report = mocker.patch(
            'opal.services.reports.ReportService.generate_questionnaire_report',
            return_value=None,
        )

        # mock an actual `translation.get_language()` call to get the language used in the current thread
        mocker.patch(
            'django.utils.translation.get_language',
            return_value=None,
        )

        self.make_request(api_client, admin_user, hospital_patient.site.code, hospital_patient.mrn)

        mock_generate_questionnaire_report.assert_called_once_with(
            QuestionnaireReportRequestData(
                patient_id=hospital_patient.patient.legacy_id,
                patient_name='Marge Simpson',
                patient_site='RVH',
                patient_mrn='9999996',
                logo_path=Path(institution.logo.path),
                language=settings.LANGUAGES[0][0],
            ),
        )

    def test_report_generation_error(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure that unsuccessful report generation is handled properly and does not cause any exceptions."""
        institution = hospital_settings_factories.Institution(pk=1)
        hospital_patient = patient_factories.HospitalPatient(
            site=patient_factories.Site(code='RVH'),
        )

        message = 'An error occurred during report generation.'
        error_response = {'status': 'error', 'message': message}

        # mock an actual call to the legacy report generation service to raise a request error
        mock_generate_questionnaire_report = mocker.patch(
            'opal.services.reports.ReportService.generate_questionnaire_report',
            return_value=None,
        )

        # mock the logger
        mock_logger = mocker.patch('logging.Logger.error', return_value=None)

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, hospital_patient.mrn)

        mock_generate_questionnaire_report.assert_called_once_with(
            QuestionnaireReportRequestData(
                patient_id=hospital_patient.patient.legacy_id,
                patient_name='Marge Simpson',
                patient_site='RVH',
                patient_mrn='9999996',
                logo_path=Path(institution.logo.path),
                language='en',
            ),
        )
        mock_logger.assert_called_once_with(message)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == error_response

    def test_report_export_error(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Ensure that unsuccessful PDF report exporting is handled properly and does not cause any exceptions."""
        base64_encoded_report = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
        hospital_settings_factories.Institution(pk=1)
        hospital_patient = patient_factories.HospitalPatient()

        message = 'An error occurred while exporting a PDF report to the OIE.'

        # mock the logger
        mock_logger = mocker.patch('logging.Logger.error', return_value=None)

        # mock an actual call to the legacy report generation service to raise a request error
        mocker.patch(
            'opal.services.reports.ReportService.generate_questionnaire_report',
            return_value=base64_encoded_report,
        )

        mock_export_pdf_report = mocker.patch(
            'opal.services.hospital.hospital.OIEService.export_pdf_report',
            return_value=None,
        )

        document_date = timezone.now().replace(microsecond=0)
        mocker.patch(
            'django.utils.timezone.now',
            return_value=document_date,
        )

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, hospital_patient.mrn)

        mock_export_pdf_report.assert_called_once_with(
            OIEReportExportData(
                mrn=hospital_patient.mrn,
                site=hospital_patient.site.code,
                base64_content=base64_encoded_report,
                document_number='MU-8624',  # TODO: clarify where to get the value
                document_date=document_date,  # TODO: get the exact time of the report creation
            ),
        )
        mock_logger.assert_called_once_with(message)
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    def test_post_report_export(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Test PDF report export request sent to the OIE."""
        base64_encoded_report = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
        hospital_settings_factories.Institution(pk=1)
        hospital_patient = patient_factories.HospitalPatient()

        # mock an actual call to the legacy report generation service to raise a request error
        mocker.patch(
            'opal.services.reports.ReportService.generate_questionnaire_report',
            return_value=base64_encoded_report,
        )

        mock_export_pdf_report = mocker.patch(
            'opal.services.hospital.hospital.OIEService.export_pdf_report',
            return_value={'status': 'success'},
        )

        document_date = timezone.now().replace(microsecond=0)
        mocker.patch(
            'django.utils.timezone.now',
            return_value=document_date,
        )

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, hospital_patient.mrn)

        mock_export_pdf_report.assert_called_once_with(
            OIEReportExportData(
                mrn=hospital_patient.mrn,
                site=hospital_patient.site.code,
                base64_content=base64_encoded_report,
                document_number='MU-8624',  # TODO: clarify where to get the value
                document_date=mocker.ANY,  # TODO: get the exact time of the report creation
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'status': 'success'}
