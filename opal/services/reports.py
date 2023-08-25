"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import json
import logging
from pathlib import Path
from typing import NamedTuple, Optional

from django.conf import settings

import requests
from fpdf import FPDF, FlexTemplate
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status

from opal.utils.base64 import Base64Util

from .pdf_generator import PDFGenerator


class QuestionnaireReportRequestData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for generating a questionnaire PDF report.

    Attributes:
        patient_id: the ID of an Opal patient (e.g., patient serial number)
        patient_name: patient's first name and last name
        patient_site: patient's site code (e.g., RVH)
        patient_mrn: patient's medical record number (e.g., 9999996) within the site
        logo_path: file path of the logo image
        language: report's language (English or French)
    """

    patient_id: int
    patient_name: str
    patient_site: str
    patient_mrn: str
    logo_path: Path
    language: str


class ReportService():
    """Service that provides functionality for generating PDF reports."""

    content_type = 'application/json'
    logger = logging.getLogger(__name__)

    # TODO: use fpdf2 instead of the legacy PDF-generator (PHP service)
    def generate_base64_questionnaire_report(
        self,
        report_data: QuestionnaireReportRequestData,
    ) -> Optional[str]:
        """Create a questionnaire PDF report in encoded base64 string format.

        Args:
            report_data: questionnaire data required to call the legacy PHP report service

        Returns:
            encoded base64 string of the generated questionnaire PDF report
        """
        # return a `None` if questionnaire report request data are not valid
        if not self._is_questionnaire_report_request_data_valid(report_data):
            self.logger.error(
                '{0} {1}'.format(
                    'The questionnaire report request data are not valid.',
                    'Please check the data that are being passed to the legacy PHP report service.',
                ),
            )
            return None

        base64_report = self._request_base64_report(report_data)

        if Base64Util().is_base64(base64_report) is True:
            return base64_report

        self.logger.error('The generated questionnaire PDF report is not in the base64 format.')
        return None

    def generate_pathology_report(
        self,
        # pathology_data: PathologyData,
    ) -> str:
        """Create a pathology PDF report.

        Args:
            pathology_data: pathology data required to generate the PDF report

        Returns:
            path to the generated pathology report
        """
        elements = [
            {'name':'box', 'type':'B', 'x1':0, 'y1':0, 'x2':50, 'y2':50,},
            {'name':'d1', 'type':'L', 'x1':0, 'y1':0, 'x2':50, 'y2':50,},
            {'name':'d2', 'type':'L', 'x1':0, 'y1':50, 'x2':50, 'y2':0,},
            {'name':'label', 'type':'T', 'x1':0, 'y1':52, 'x2':50, 'y2':57, 'text':'Label',},
        ]
        pdf = PDFGenerator()
        pdf.add_page()
        templ = FlexTemplate(pdf, elements)
        templ['label'] = 'Offset: 50 / 50 mm'
        templ.render(offsetx=50, offsety=50)
        templ['label'] = 'Offset: 50 / 120 mm'
        templ.render(offsetx=50, offsety=120)
        templ['label'] = 'Offset: 120 / 50 mm, Scale: 0.5'
        templ.render(offsetx=120, offsety=50, scale=0.5)
        templ['label'] = 'Offset: 120 / 120 mm, Rotate: 30°, Scale=0.5'
        templ.render(offsetx=120, offsety=120, rotate=30.0, scale=0.5)
        pdf.output('example.pdf')
        return ''

    def _request_base64_report(
        self,
        report_data: QuestionnaireReportRequestData,
    ) -> Optional[str]:
        """Generate a PDF report by making an HTTP call to the legacy PHP endpoint.

        Args:
            report_data (QuestionnaireReportRequestData): report request data needed to call legacy PHP report service

        Returns:
            str: encoded base64 string of the generated PDF report
        """
        payload = json.dumps({
            'patient_id': report_data.patient_id,
            'patient_name': report_data.patient_name,
            'patient_site': report_data.patient_site,
            'patient_mrn': report_data.patient_mrn,
            'logo_base64': Base64Util().encode_to_base64(report_data.logo_path),
            'language': report_data.language,
        })

        headers = {'Content-Type': self.content_type}

        try:
            response = requests.post(
                url=settings.LEGACY_QUESTIONNAIRES_REPORT_URL,
                headers=headers,
                data=payload,
                timeout=60,
            )
        except RequestException:
            self.logger.exception('An error occurred while requesting the legacy PHP report service.')
            return None

        # Return a `None` if response status code is not success (e.g., different than 2**)
        if status.is_success(response.status_code) is False:
            self.logger.error(
                'The status code of the response from the PHP report service should be "200".\n{0}\n{1}'.format(
                    response.reason,
                    response.text,
                ),
            )
            return None

        # Return a `None` string if cannot read encoded pdf report
        try:
            base64_report = response.json()['data']['base64EncodedReport']
        except (KeyError, JSONDecodeError):
            self.logger.exception(
                '{0} {1}'.format(
                    'Cannot read "base64EncodedReport" key in the JSON response received from PHP report service.\n',
                    response.text,
                ),
            )
            return None

        # Check if ['data']['base64EncodedReport'] is a string and return its value. If not a string, return `None`.
        if isinstance(base64_report, str):
            return base64_report

        self.logger.error('The "base64EncodedReport" value received from the PHP report service is not a string.')
        return None

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

        return (  # check if patient_id is a positive number
            report_data.patient_id >= 0
            # check if logo_path exists
            and report_data.logo_path.exists()
            # check if language exists
            and report_data.language in languages
        )
