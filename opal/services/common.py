"""Module providing business logic for generating PDF reports using fpdf2 library."""

import json
import logging
import math
import textwrap
from datetime import date
from pathlib import Path
from typing import Any, Literal, NamedTuple

from django.conf import settings

import requests
from fpdf import FPDF, Align, FlexTemplate
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status
from typing_extensions import TypedDict

from opal.utils.base64_util import Base64Util


class FPDFCellDictType(TypedDict):
    """The required arguments to pass to FPDF's cell() function."""

    w: float | None  # noqa: WPS111
    h: float | None  # noqa: WPS111
    text: str
    border: bool | str | Literal[0, 1]
    align: str | Align


class FPDFMultiCellDictType(TypedDict):
    """The required arguments to pass to FPDF's multi_cell() function."""

    w: float  # noqa: WPS111
    h: float | None  # noqa: WPS111
    text: str
    align: str | Align


class FPDFFontDictType(TypedDict):
    """The required arguments to pass to FPDF's set_font() function."""

    family: str | None
    style: Literal['', 'B', 'I', 'U', 'BU', 'UB', 'BI', 'IB', 'IU', 'UI', 'BIU', 'BUI', 'IBU', 'IUB', 'UBI', 'UIB']
    size: int


class FPDFRectDictType(TypedDict):
    """The required arguments to pass to FPDF's rect() function."""

    x: float  # noqa: WPS111
    y: float  # noqa: WPS111
    w: float  # noqa: WPS111
    h: float  # noqa: WPS111
    style: str | None


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


class InstitutionData(NamedTuple):
    """Information about an institution from which a report was received.

    Attributes:
        institution_logo_path: file path of the instituion's logo image
    """

    institution_logo_path: Path


class SiteData(NamedTuple):
    """Information about a hospital site from which a report was received.

    Attributes:
        site_name: the name of the site (e.g., Royal Victoria Hospital)
        site_building_address: the building address of the site (e.g., 1001, boulevard Décarie)
        site_city: the name of the city that is specified in the address (e.g., Montréal)
        site_province: the name of the province that is specified in the address (e.g., Québec)
        site_postal_code: the postal code that specified in the address (e.g., H4A3J1)
        site_phone: the phone number that is specified in the address (e.g., 514 934 4400)
    """

    site_name: str
    site_building_address: str
    site_city: str
    site_province: str
    site_postal_code: str
    site_phone: str


class PatientData(NamedTuple):
    """Information about a patient for whom a report was received.

    Attributes:
        patient_first_name: patient's first name (e.g., Marge)
        patient_last_name: patient's last name (e.g., Simpson)
        patient_date_of_birth: patient's birth date (e.g., 03/19/1986)
        patient_ramq: patient's RAMQ number (SIMM99999999)
        patient_sites_and_mrns: patient's sites and MRNs => [{'mrn': 'X', 'site_code': '1'}]
    """

    patient_first_name: str
    patient_last_name: str
    patient_date_of_birth: date
    patient_ramq: str
    patient_sites_and_mrns: list[dict[str, str]]


FIRST_PAGE_NUMBER: int = 1
PATHOLOGY_REPORT_FONT: str = 'helvetica'


class ReportPDF(FPDF):  # noqa: WPS214
    """Customized FPDF class that provides implementation for generating PDF reports."""

    def __init__(
        self,
        institution_data: InstitutionData,
        patient_data: PatientData,
        site_data: SiteData,
        report_data: Any,
    ) -> None:
        """Initialize a `PDF` instance for generating reports.

        The initialization consists of 3 steps:
            - Initialization of the `FPDF` instance
            - Setting the PDF's metadata (e.g., author, creation date, keywords, etc.)
            - Generating the PDF by using FPDF's templates

        Args:
            institution_data: institution data required to generate the PDF report
            patient_data: patient data required to generate the PDF report
            site_data: site data required to generate the PDF report
            report_data: data required to generate the PDF report
        """
        super().__init__()
        self.institution_data = institution_data
        self.site_data = site_data
        self.patient_data = patient_data
        self.report_data = report_data
        self.patient_name = f'{patient_data.patient_last_name}, {patient_data.patient_first_name}'.upper()
        # Concatenated patient's site codes and MRNs for the header.
        sites_and_mrns_list = [
            f'{site_mrn["site_code"]}-{site_mrn["mrn"]}' for site_mrn in self.patient_data.patient_sites_and_mrns
        ]
        self.patient_sites_and_mrns_str = ', '.join(
            sites_and_mrns_list,
        )

    def add_page(self, *args: Any, **kwargs: Any) -> None:
        """Add new page to the pathology report and draw the frame if not the first page.

        Args:
            args: varied amount of non-keyword arguments
            kwargs: varied amount of keyword arguments
        """
        super().add_page(*args, **kwargs)

        if self.page != FIRST_PAGE_NUMBER:
            header_cursor_abscissa_position_in_mm: int = 40
            # Set the cursor at the top (e.g., 4 cm from the top).
            self.set_y(header_cursor_abscissa_position_in_mm)

    def _draw_institution_logo(self) -> None:
        """Draw the institution logo that is shown at the top of the first page."""
        self.image(
            str(self.institution_data.institution_logo_path),
            x=35,
            y=15,
            w=120,
            h=30,
        )

    def _draw_site_address_and_patient_table(self) -> None:
        """Draw the site address and patient info table."""
        site_patient_box = FlexTemplate(self, self._get_site_address_patient_info_box())
        site_patient_box.render()
        # Draw the border/frame around the site address and patient info table.
        border_around_site = FPDFRectDictType(
            x=15,
            y=45,
            w=180,
            h=self.get_y() - 40,
            style='D',
        )
        bottom_line_of_the_border = {
            'x1': 105,
            'y1': 45,
            'x2': 105,
            'y2': self.get_y() + 5,
        }
        self.set_line_width(width=0.5)
        self.rect(**border_around_site)
        self.line(**bottom_line_of_the_border)

    def _get_site_address_patient_info_box(self) -> list[dict[str, Any]]:   # noqa: WPS210
        """Build a table/box that is shown at the top of the first page.

        The table contains site's and patient's information.

        Returns:
            dictionary containing data needed to build a table that is shown at the top of the first page.
        """
        sites_and_mrns = self.patient_data.patient_sites_and_mrns
        mrns_and_sites_multiline = '\n'.join(
            [f'{site_mrn["site_code"]}# : {site_mrn["mrn"]}' for site_mrn in sites_and_mrns],
        )
        site_city = (
            f'{self.site_data.site_city} '
            + f'({self.site_data.site_province}) '
            + f'{self.site_data.site_postal_code}'
        ) if str(self.site_data.site_city) else ''
        site_phone = (
            f'Tél. : {self.site_data.site_phone}'
        ) if str(self.site_data.site_phone) else ''

        # Wrap the text with the maximum characters can be filled in each line.
        wrapper = textwrap.TextWrapper(
            width=int((185 - 110) / 2) - 1,
        )
        patient_name = wrapper.fill(text=f'Nom/Name: {self.patient_name}')
        # Calculate the number of the lines patient name will occupy
        line = math.ceil(len(patient_name) * 2 / (185 - 110))
        return [
            {
                'name': 'site_name',
                'type': 'T',
                'x1': 20,
                'y1': 47,
                'x2': 125,
                'y2': 52,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.site_data.site_name,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'site_building_address',
                'type': 'T',
                'x1': 20,
                'y1': 52,
                'x2': 125,
                'y2': 57,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.site_data.site_building_address,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'site_city',
                'type': 'T',
                'x1': 20,
                'y1': 56,
                'x2': 125,
                'y2': 61,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': site_city,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'site_phone',
                'type': 'T',
                'x1': 20,
                'y1': 60,
                'x2': 125,
                'y2': 65,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': site_phone,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'patient_name',
                'type': 'T',
                'x1': 110,
                'y1': 47,
                'x2': 185,
                'y2': 51,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': patient_name,
                'priority': 0,
                'multiline': True,
            },
            {
                'name': 'patient_date_of_birth',
                'type': 'T',
                'x1': 110,
                'y1': 47 + 4 * line,
                'x2': 185,
                'y2': 47 + 4 * (line + 1),
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': f'DDN/DOB: {self.patient_data.patient_date_of_birth.strftime("%m/%d/%Y")}',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'patient_ramq',
                'type': 'T',
                'x1': 110,
                'y1': 47 + 4 * (line + 1),
                'x2': 185,
                'y2': 47 + 4 * (line + 2),
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': f'NAM/RAMQ: {self.patient_data.patient_ramq}',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'patient_sites_and_mrns',
                'type': 'T',
                'x1': 110,
                'y1': 47 + 4 * (line + 2),
                'x2': 185,
                'y2': 47 + 4 * (line + 3),
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': mrns_and_sites_multiline,
                'priority': 0,
                'multiline': True,
            },
        ]


class ReportService():
    """Service that provides functionality for generating PDF reports."""

    content_type = 'application/json'
    logger = logging.getLogger(__name__)

    # TODO: use fpdf2 instead of the legacy PDF-generator (PHP service)
    def generate_base64_questionnaire_report(
        self,
        report_data: QuestionnaireReportRequestData,
    ) -> str | None:
        """Create a questionnaire PDF report in encoded base64 string format.

        Args:
            report_data: questionnaire data required to call the legacy PHP report service

        Returns:
            encoded base64 string of the generated questionnaire PDF report
        """
        # return a `None` if questionnaire report request data are not valid
        if not self._is_questionnaire_report_request_data_valid(report_data):
            self.logger.error(
                'The questionnaire report request data are not valid.'
                + 'Please check the data that are being passed to the legacy PHP report service.',
            )
            return None

        base64_report = self._request_base64_report(report_data)

        if Base64Util().is_base64(base64_report) is True:
            return base64_report

        self.logger.error('The generated questionnaire PDF report is not in the base64 format.')
        return None

    def _request_base64_report(
        self,
        report_data: QuestionnaireReportRequestData,
    ) -> str | None:
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
                'The status code of the response from the PHP report service should be "200".\n'
                + f'{response.reason}\n{response.text}',
            )
            return None

        # Return a `None` string if cannot read encoded pdf report
        try:
            base64_report = response.json()['data']['base64EncodedReport']
        except (KeyError, JSONDecodeError):
            self.logger.exception(
                'Cannot read "base64EncodedReport" key in the JSON response received from PHP report service.\n'
                + f' {response.text}',
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
