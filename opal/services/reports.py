"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple, Optional

from django.conf import settings

import requests
from fpdf import FPDF
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status

from opal.utils.base64 import Base64Util


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


class PathologyData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for generating a pathology PDF report.

    Attributes:
        site_logo_path: file path of the site's logo image
        site_name: the name of the site (e.g., Royal Victoria Hospital)
        site_building_address: the building address of the site (e.g., 1001, boulevard Décarie)
        site_city: the name of the city that is specified in the address (e.g., Montréal)
        site_province: the name of the province that is specified in the address (e.g., Québec)
        site_postal_code: the postal code that specified in the address (e.g., H4A 3J1)
        site_phone: the phone number that is specified in the address (e.g., 514 934 4400)
        patient_name: patient's last name and first name separated by comma (e.g., SIMPSON, MARGE)
        patient_date_of_birth: patient's birth date (e.g., 03/19/1986)
        patient_ramq: patient's RAMQ number (SIMM99999999)
        patient_mrns: patient's sites and MRNs => [{'mrn': 'X', 'site_code': '1'}, {'mrn_site': 'Y', 'site_code': '2'}]
        test_number: the report number (e.g., AS-2021-62605)
        test_collected_at: date and time when the specimen was collected (e.g., 2021-Nov-25 09:55)
        test_reported_at: date and time when the specimen was reported (e.g., 2021-Nov-28 11:52)
        observation_clinical_info: list of clinical information recrods (e.g., ['first record', 'second record'])
        observation_specimens: list of specimen records (e.g, ['specimen one', 'specimen two'])
        observation_descriptions: list of observation descriptions (e.g., ['description one', 'description two'])
        observation_diagnosis: list of observation diagnosis (e.g., ['diagnosis one', 'diagnosis two'])
        prepared_by: the name of the person who prepared the report (e.g., Atilla Omeroglu, MD)
        prepared_at: the date and time when the report was prepared (e.g., 28-Nov-2021 11:52am)
    """

    site_logo_path: Path
    site_name: str
    site_building_address: str
    site_city: str
    site_province: str
    site_postal_code: str
    site_phone: str
    patient_name: str
    patient_date_of_birth: date
    patient_ramq: str
    patient_mrns: list[dict[str, str]]
    test_number: str
    test_collected_at: str
    test_reported_at: datetime
    observation_clinical_info: list[str]
    observation_specimens: list[str]
    observation_descriptions: list[str]
    observation_diagnosis: list[str]
    prepared_by: str
    prepared_at: datetime


class PathologyPDF(FPDF):
    """Class that provides a base setup for the pathology PDF generation."""

    def header(self) -> None:
        """Set PDF header."""
        # Setting font: helvetica bold 15
        self.set_font('helvetica', 'B', 15)  # noqa: WPS432
        # Moving cursor to the right:
        self.cell(w=80)  # noqa: WPS432
        # Printing title:
        self.cell(30, 10, 'Title', border=1, align='C')  # noqa: WPS432
        # Performing a line break:
        self.ln(h=20)  # noqa: WPS432

    def footer(self) -> None:
        """Set PDF footer."""
        # Position cursor at 1.5 cm from bottom:
        self.set_y(y=-15)  # noqa: WPS432
        # Setting font: helvetica italic 8
        self.set_font(
            family='arial',
            style='B',
            size=12,  # noqa: WPS432
        )
        # Printing page number:
        self.cell(
            w=0,
            h=10,
            txt=f'Page {self.page_no()}/{{nb}}',
            border='B',
            align='R',
        )


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
        pathology_data: PathologyData,
    ) -> Path:
        """Create a pathology PDF report.

        Args:
            pathology_data: pathology data required to generate the PDF report

        Returns:
            path to the generated pathology report
        """
        pdf = PathologyPDF()
        pdf.add_page()
        # TODO: fix file name
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_path = settings.PATHOLOGY_REPORTS_PATH / f'{str(generated_at)}.pdf'
        pdf.output(str(report_path))
        return report_path

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
