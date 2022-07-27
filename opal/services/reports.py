"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import json
from pathlib import Path
from typing import NamedTuple

from django.conf import settings

import requests
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status

from opal.legacy.models import LegacyPatient
from opal.utils.base64_util import Base64Util


class QuestionnaireReportRequestData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for generating a questionnaire PDF report.

    Attributes:
        patient_id (int): the ID of an Opal patient (e.g., patient serial number)
        logo_path (Path): file path of the logo image
        language (str): report's language (English or French)
    """

    patient_id: int
    logo_path: Path
    language: str


class ReportService():
    """Service that provides functionality for generating questionnaire pdf reports."""

    content_type = 'application/json'

    def generate_questionnaire_report(
        self,
        report_data: QuestionnaireReportRequestData,
    ) -> str:
        """Create PDF report in encoded base64 string format.

        Args:
            report_data (QuestionnaireReportRequestData): report request data needed to call legacy PHP report service

        Returns:
            str: encoded base64 string of the generated PDF report
        """
        # return an empty string if questionnaire report request data is not valid
        if not self._is_questionnaire_report_request_data_valid(report_data):
            return ''

        base64_report = self._request_base64_report(report_data)

        return base64_report if Base64Util().is_base64(base64_report) is True else ''

    def _request_base64_report(
        self,
        report_data: QuestionnaireReportRequestData,
    ) -> str:
        """Generate a PDF report by making an HTTP call to the legacy PHP endpoint.

        Args:
            report_data (QuestionnaireReportRequestData): report request data needed to call legacy PHP report service

        Returns:
            str: encoded base64 string of the generated PDF report
        """
        payload = json.dumps({
            'patient_id': report_data.patient_id,
            'logo_base64': Base64Util().encode_image_to_base64(report_data.logo_path),
            'language': report_data.language,
        })

        headers = {'Content-Type': self.content_type}

        try:
            response = requests.post(
                url=settings.LEGACY_QUESTIONNAIRES_REPORT_URL,
                headers=headers,
                data=payload,
            )
        except RequestException:
            return ''

        # Return an empty string if response status code is not success (e.g, different than 2**)
        if status.is_success(response.status_code) is False:
            return ''

        # Return an empty string if cannot read encoded pdf report
        try:
            base64_report = response.json()['data']['base64EncodedReport']
        except (KeyError, JSONDecodeError):
            return ''

        # Check if ['data']['base64EncodedReport'] is a string and return its value. If not a string, return empty one.
        return base64_report if isinstance(base64_report, str) else ''

    def _is_questionnaire_report_request_data_valid(
        self,
        report_data: QuestionnaireReportRequestData,
    ) -> bool:
        """Check if questionnaire report request data is valid.

        Args:
            report_data (QuestionnaireReportRequestData): report request data needed to call legacy PHP report service

        Returns:
            bool: boolean value showing if questionnaire report request data is valid
        """
        languages = dict(settings.LANGUAGES)

        return (  # check if patient_id (PatientSerNum) exists
            LegacyPatient.objects.filter(patientsernum=report_data.patient_id).exists()
            # check if logo_path exists
            and report_data.logo_path.exists()
            # check if language exists
            and report_data.language in languages
        )
