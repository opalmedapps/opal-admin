from pathlib import Path
from typing import Any

from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

import pytest
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

    def test_mrn_not_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an MRN that doesn't exist."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, 'wrong mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Provided MRN does not exist.' in str(response.data['mrn'])

    def test_no_mrn(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty MRN."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, '')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['mrn'])

    def test_invalid_site_length(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a site code that has more than 100 characters."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(
            api_client,
            admin_user,
            get_random_string(length=101),
            hospital_patient.mrn,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 100 characters.' in str(response.data['site'])

    def test_site_not_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a site code that doesn't exist."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, 'invalid site', hospital_patient.mrn)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Provided site code does not exist.' in str(response.data['site'])

    def test_no_site(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty site code."""
        hospital_patient = patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, '', hospital_patient.mrn)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['site'])

    def test_invalid_site_mrn_length(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an MRN that has more than 10 characters and a site code that has more than 100 characters."""
        response = self.make_request(api_client, admin_user, get_random_string(length=101), 'invalid mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ensure this field has no more than 100 characters.' in str(response.data['site'])
        assert 'Ensure this field has no more than 10 characters.' in str(response.data['mrn'])

    def test_site_mrn_not_found(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing a site code and an MRN that do not exist."""
        patient_factories.HospitalPatient()

        response = self.make_request(api_client, admin_user, 'invalid site', 'wrong mrn')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Provided site code does not exist.' in str(response.data['site'])
        assert 'Provided MRN does not exist.' in str(response.data['mrn'])

    def test_no_site_mrn(self, api_client: APIClient, admin_user: User) -> None:
        """Test providing an empty site code and MRN."""
        response = self.make_request(api_client, admin_user, '', '')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'This field may not be blank.' in str(response.data['site'])
        assert 'This field may not be blank.' in str(response.data['mrn'])

    def test_missing_hospital_patient_data(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
    ) -> None:
        """Ensure that missing `HospitalPatient` data are handled properly."""
        hospital_settings_factories.Institution(pk=1)
        hospital_patient = patient_factories.HospitalPatient()
        hospital_patient.patient.legacy_id = ''

        message = 'Could not find `HospitalPatient` object data.'
        error_response = {'status': 'error', 'message': message}

        # mock `HospitalPatient's` `get_hospital_patient_by_site_mrn` request
        mock_get_hospital_patient_by_site_mrn_first = mocker.patch(
            'django.db.models.QuerySet.first',
            return_value=None,
        )

        # mock the logger
        mock_logger = mocker.patch('logging.Logger.error', return_value=None)

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, hospital_patient.mrn)

        mock_get_hospital_patient_by_site_mrn_first.assert_called_once()

        mock_logger.assert_called_once_with(message)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == error_response

    def test_unset_language(
        self,
        api_client: APIClient,
        admin_user: User,
        mocker: MockerFixture,
        settings: SettingsWrapper,
    ) -> None:
        """Ensure that unset language is handled properly and does not throw an exception."""
        settings.LANGUAGES = []
        settings.LANGUAGE_CODE = None

        institution = hospital_settings_factories.Institution(pk=1)
        hospital_patient = patient_factories.HospitalPatient()

        # mock an actual call to the legacy report generation service to raise a request error
        mock_generate_questionnaire_report = mocker.patch(
            'opal.services.reports.ReportService.generate_questionnaire_report',
            return_value=None,
        )

        self.make_request(api_client, admin_user, hospital_patient.site.code, hospital_patient.mrn)

        mock_generate_questionnaire_report.assert_called_once_with(
            QuestionnaireReportRequestData(
                patient_id=hospital_patient.patient.legacy_id,
                logo_path=Path(institution.logo.path),
                language='EN',
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
        hospital_patient = patient_factories.HospitalPatient()

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

        document_date = timezone.localtime(timezone.now())
        mocker.patch(
            'django.utils.timezone.localtime',
            return_value=document_date,
        )

        response = self.make_request(api_client, admin_user, hospital_patient.site.code, hospital_patient.mrn)

        mock_export_pdf_report.assert_called_once_with(
            OIEReportExportData(
                mrn=hospital_patient.mrn,
                site=hospital_patient.site.code,
                base64_content=base64_encoded_report,
                document_number='FMU',  # TODO: clarify where to get the value
                document_date=document_date,  # TODO: get the exact time of the report creation
            ),
        )
        mock_logger.assert_called_once_with(message)
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None
