"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple, Optional

from django.conf import settings

import requests
from fpdf import FPDF, FlexTemplate
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
        patient_first_name: patient's first name (e.g., Marge)
        patient_last_name: patient's last name (e.g., Simpson)
        patient_date_of_birth: patient's birth date (e.g., 03/19/1986)
        patient_ramq: patient's RAMQ number (SIMM99999999)
        patient_sites_and_mrns: patient's sites and MRNs => [{'mrn': 'X', 'site_code': '1'}]
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
    patient_first_name: str
    patient_last_name: str
    patient_date_of_birth: date
    patient_ramq: str
    patient_sites_and_mrns: list[dict[str, str]]
    test_number: str
    test_collected_at: datetime
    test_reported_at: datetime
    observation_clinical_info: list[str]
    observation_specimens: list[str]
    observation_descriptions: list[str]
    observation_diagnosis: list[str]
    prepared_by: str
    prepared_at: datetime


class PathologyPDF(FPDF):
    """Customized FPDF class that provides implementation for generating pathology PDF reports."""

    def __init__(
        self,
        patient_name: str,
        patient_mrns: list[dict[str, str]],
    ) -> None:
        self.patient_name = patient_name
        self.patient_mrns = patient_mrns
        super().__init__()


    def header(self) -> None:
        """Set PDF header."""
        self.set_font(family='helvetica', size=12)
        if self.page != 1:
            self.set_font(family='helvetica', style='B', size=6)
            self.cell(
                w=0,
                align='L',
                txt='Pathologie Chirurgicale Raport (suite)',
            )

            self.ln(3)
            self.set_font(family='helvetica', size=6)
            self.cell(
                w=0,
                align='L',
                txt='Surgical Pathology Final Report (continuation)',
            )

            self.ln(7)
            self.set_font(family='helvetica', style='B', size=8)
            sites_mrns = ''.join([f'{site_mrn["site_code"]}-{site_mrn["mrn"]}' for site_mrn in self.patient_mrns])
            self.cell(
                w=0,
                align='L',
                txt=f'Patient : {self.patient_name} [{sites_mrns}]',
            )


    def footer(self) -> None:
        """Set PDF footer."""
        # Position cursor at 4 cm from bottom:
        self.set_y(y=-40)  # noqa: WPS432
        # Setting font: arial 8
        self.set_font(family='helvetica', size=8)  # noqa: WPS432

        footer_text = '{0}{1}{2}{3}{4}{5}'.format(
            "Ce raport a été généré par Opal à partir des données du système RIS de l'hôpital.",
            "Les données ne sont pas traduites et vous sont communiquées telles qu'elles sont stockées dans ",
            "le système de l'hôpital. Elles sont destinées à l'information des patients et non à un usage clinique.\n",
            "This report was generated by Opal from the hospital's RIS system data. The data is not translated, and ",
            "is being shared with you as it is stored in the hospital's system. For patient information, not for ",
            'clinical use.',
        )
        self.multi_cell(
            w=0,
            align='L',
            txt=footer_text,
        )

        # Performing a line break:
        self.ln(h=5)  # noqa: WPS432
        self.set_font(family='helvetica', style='B', size=10)
        # Printing page number:
        self.cell(
            w=0,
            h=10,
            txt=f'Page {self.page_no()}/{{nb}}',
            border='B',
            align='R',
        )

    def add_page(self) -> None:
        """Add new page to the document."""
        super().add_page()
        if self.page != 1:
            self.rect(15, 30, 180, 220, 'D')


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
        # This will define the elements that will compose the template.
        elements = [
            { 'name': 'site_patient_box', 'type': 'B', 'x1': 15.0, 'y1': 15.0, 'x2': 195.0, 'y2': 50.0, 'font': 'helvetica', 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'C', 'text': None, 'priority': 0, 'multiline': False},
            { 'name': 'site_patient_box_separator', 'type': 'L', 'x1': 135.0, 'y1': 15.0, 'x2': 135.0, 'y2': 50.0, 'font': 'helvetica', 'size': 0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'C', 'text': None, 'priority': 3, 'multiline': False},
            { 'name': 'site_logo', 'type': 'I', 'x1': 45.0, 'y1': 17.0, 'x2': 105.0, 'y2': 30.0, 'font': None, 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'C', 'text': 'logo', 'priority': 2, 'multiline': False},
            { 'name': 'site_name', 'type': 'T', 'x1': 20.0, 'y1': 30.0, 'x2': 125.0, 'y2': 35.0, 'font': 'helvetica', 'size': 10.0, 'bold': 1, 'italic': 0, 'underline': 0, 'align': 'L', 'text': '', 'priority': 2, 'multiline': False},
            { 'name': 'site_building_address', 'type': 'T', 'x1': 20.0, 'y1': 35.0, 'x2': 125.0, 'y2': 40.0, 'font': 'helvetica', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'L', 'text': '', 'priority': 2, 'multiline': False},
            { 'name': 'site_city', 'type': 'T', 'x1': 20.0, 'y1': 39.0, 'x2': 125.0, 'y2': 44.0, 'font': 'helvetica', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'L', 'text': '', 'priority': 2, 'multiline': False},
            { 'name': 'site_phone', 'type': 'T', 'x1': 20.0, 'y1': 43.0, 'x2': 125.0, 'y2': 48.0, 'font': 'helvetica', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'L', 'text': '', 'priority': 2, 'multiline': False},
            # TODO: use get_x() and get_y()
            # TODO: handle long patient names, this might affect the starting position of the patient_date_of_birth
            { 'name': 'patient_name', 'type': 'T', 'x1': 138, 'y1': 30.0, 'x2': 190.0, 'y2': 34.0, 'font': 'helvetica', 'size': 9.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'L', 'text': '', 'priority': 2, 'multiline': False},
            { 'name': 'patient_date_of_birth', 'type': 'T', 'x1': 138, 'y1': 34.0, 'x2': 190.0, 'y2': 38.0, 'font': 'helvetica', 'size': 9.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'L', 'text': '', 'priority': 2, 'multiline': False},
            { 'name': 'patient_ramq', 'type': 'T', 'x1': 138, 'y1': 38.0, 'x2': 190.0, 'y2': 42.0, 'font': 'helvetica', 'size': 9.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'L', 'text': '', 'priority': 2, 'multiline': False},
            # { 'name': 'multline_text', 'type': 'T', 'x1': 20, 'y1': 100, 'x2': 40, 'y2': 105, 'font': 'helvetica', 'size': 12, 'bold': 0, 'italic': 0, 'underline': 0, 'background': 0x88ff00, 'align': 'C', 'text': 'Lorem ipsum dolor sit amet, consectetur adipisici elit', 'priority': 2, 'multiline': True},
        ]
        # TODO: use will_page_break()
        pdf = PathologyPDF(
            patient_name=pathology_data.patient_name,
            patient_mrns=pathology_data.patient_mrns,
        )
        # Set PDF's metadata
        pdf.set_author('Opal Health Informatics Group')
        pdf.set_creation_date(datetime.now())
        pdf.set_creator('Opal Backend')
        pdf.set_keywords(
            'Pathology Report, Pathologie Chirurgicale Rapport Final, Surgical Pathology Final Report, Opal, Opal Health Informatics Group',
        )
        pdf.set_subject(f'Pathology report for {pathology_data.patient_name}')
        pdf.set_title('Pathologie Chirurgicale Rapport Final/Surgical Pathology Final Report')
        pdf.set_producer('fpdf2 2.7.5')  # TODO: get the version automatically
        pdf.add_page()
        templ = FlexTemplate(pdf, elements)
        templ['site_name'] = 'Royal Victoria Hospital'
        templ['site_logo'] = pathology_data.site_logo_path
        templ['site_building_address'] = '1001, boulevard Décarie'
        templ['site_city'] = 'Montréal (Québec) H4A 3J1'
        templ['site_phone'] = 'Tél. : 514 934 4400'
        templ['patient_name'] = f'Nom/Name: {pathology_data.patient_name}'
        templ['patient_date_of_birth'] = f'DDN/DOB: {pathology_data.patient_date_of_birth.strftime("%m/%d/%Y")}'
        templ['patient_ramq'] = f'NAM/RAMQ: {pathology_data.patient_ramq}'
        templ.render()
        pdf.add_page()

        # # TODO: fix file name
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_path = settings.PATHOLOGY_REPORTS_PATH / f'{str(generated_at)}.pdf'
        pdf.output('report.pdf')

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
