"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import json
import logging
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, NamedTuple

from django.conf import settings
from django.utils import timezone

import requests
from fpdf import FPDF, FPDF_VERSION, Align, TitleStyle, enums
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

# TODO: Correctly define the questionnaireData with it's appropriate attributes


class QuestionnaireData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for generating a questionnaire PDF report.

    Attributes:
        prepared_by: the name of the person who prepared the report (e.g., Atilla Omeroglu, MD)
        prepared_at: the date and time when the report was prepared (e.g., 28-Nov-2021 11:52am)
    """

    prepared_by: str
    prepared_at: datetime


FIRST_PAGE_NUMBER: int = 1
QUESTIONNAIRE_REPORT_FONT: str = 'Times'

# TODO: Add query for all the the completed questionnaire data of the patient
QUESTIONNAIRE_DATA = ()
UPDATE_DATA = ()

# Subject to changes once the data is correctly imported
sorted_data = sorted(  # type: ignore[var-annotated]
    zip(QUESTIONNAIRE_DATA, UPDATE_DATA),
    key=lambda sort: datetime.strptime(sort[1], '%Y-%m-%d %H:%M'),
    reverse=True,
)

TABLE_DATA = {}  # noqa: WPS407

for title, update_date in sorted_data:
    last_updated = datetime.strptime(update_date, '%Y-%m-%d %H:%M')
    formatted_date = last_updated.strftime('%Y-%b-%d %H:%M')
    TABLE_DATA[title] = (title, formatted_date)


TABLE_HEADER = ('Questionnaires remplis', 'Dernière mise à jour', 'Page')


class QuestionnairePDF(FPDF):  # noqa: WPS214
    """Customized FPDF class that provides implementation for generating questionnaire PDF reports."""

    def __init__(
        self,
        institution_data: InstitutionData,
        patient_data: PatientData,
        site_data: SiteData,
        questionnaire_data: QuestionnaireData,
    ) -> None:
        """Initialize a `QuestionnairePDF` instance for generating questionnaire reports.

        The initialization consists of 3 steps:
            - Initialization of the `FPDF` instance
            - Setting the PDF's metadata (e.g., author, creation date, keywords, etc.)
            - Generating the PDF by using FPDF's templates

        Args:
            institution_data: institution data required to generate the PDF report
            site_data: site data required to generate the PDF report
            patient_data: patient data required to generate the PDF report
            questionnaire_data: questionnaire data required to generate the PDF report
        """
        super().__init__()
        self.institution_data = institution_data
        self.site_data = site_data
        self.patient_data = patient_data
        self.questionnaire_data = questionnaire_data
        self.patient_name = f'{patient_data.patient_last_name}, {patient_data.patient_first_name}'.upper()
        # Concatenated patient's site codes and MRNs for the header.
        sites_and_mrns_list = [
            f'{site_mrn["site_code"]}: {site_mrn["mrn"]}'
            for site_mrn in self.patient_data.patient_sites_and_mrns
            if site_mrn['site_code'] == 'RVH'
        ]
        self.patient_sites_and_mrns_str = ', '.join(
            sites_and_mrns_list,
        )
        auto_page_break_bottom_margin: int = 50

        self._set_report_metadata()
        self.set_auto_page_break(auto=True, margin=auto_page_break_bottom_margin)
        self.add_page()
        self._generate()

    def header(self) -> None:  # noqa: WPS213
        """Set the questionnaire PDF's header.

        This is automatically called by FPDF.add_page() and should not be called directly by the user application.
        """
        header_patient_info = FPDFCellDictType(
            w=0,
            h=0,
            align='R',
            border=0,
            text=f'{self.patient_data.patient_first_name} {self.patient_data.patient_last_name}',
        )
        header_text_rvh = FPDFCellDictType(
            w=0,
            h=0,
            align='R',
            border=0,
            text=f'{self.patient_sites_and_mrns_str}',
        )
        header_title = FPDFCellDictType(
            w=0,
            h=0,
            align='L',
            border=0,
            text='Questionnaires remplis et déclarés par le patient',
        )
        header_toc_link = FPDFCellDictType(
            w=0,
            h=0,
            align='L',
            border=0,
            text='Back to Table of Contents',
        )
        self.image(
            (self.institution_data.institution_logo_path),
            x=5,
            y=5,
            w=60,
            h=12,
        )
        self.set_y(y=5)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=15)
        self.cell(**header_patient_info)
        self.ln(6)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=15)
        self.cell(70)
        self.cell(**header_text_rvh)

        self.ln(11)
        self.cell(8)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=15)
        self.set_x(10)
        self.cell(**header_title)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='U', size=10)
        self.set_text_color(0, 0, 255)
        self.set_x(160)
        self.cell(**header_toc_link, link=self.add_link(page=1))  # type: ignore[arg-type]

        self.line(10, 18, 200, 18)  # X1, Y1, X2, Y2

        self.line(10, 26, 200, 26)  # X1, Y1, X2, Y2

    def footer(self) -> None:  # noqa: WPS213
        """Set the questionnaire PDF's footer.

        This is automatically called by FPDF.add_page() and FPDF.output().

        It should not be called directly by the user application.
        """
        # Move the cursor to the bottom (e.g., 4 cm from the bottom).
        footer_text: str = (
            'Si une version papier de ce document est reçue aux archives, avec ou sans notes manuscrites, en statut'
            + ' préliminaire ou final, **il ne sera pas numérisé.** '
            + 'Les corrections doivent être faites dans le document préliminaire'
            + " ou via l \'addendum si le document est final.\n"
            + '\n'
            + 'If a printout of this document is received in Medical Records, with or without'
            + 'handwritten notes, whether it is preliminary or final, **it will not be scanned.** '
            + 'Corrections must be done in the preliminary document or via an addendum if the document is final.\n'
        )
        footer_block = FPDFMultiCellDictType(w=190, h=None, align='L', text=footer_text)
        footer_page = FPDFCellDictType(
            w=0,
            h=5,
            text=f'Page {self.page_no()} de {{nb}}',
            border=0,
            align='R',
        )
        footer_fmu_date = FPDFCellDictType(
            w=0,
            h=5,
            text='Tempory text',
            border=0,
            align='L',
        )
        self.line(10, 260, 200, 260)
        self.set_y(y=-35)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=12)
        self.cell(**footer_fmu_date)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='', size=12)
        self.cell(**footer_page)
        self.ln(10)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, size=9)
        self.multi_cell(**footer_block, markdown=True)

    def add_page(self, *args: Any, **kwargs: Any) -> None:
        """Add new page to the pathology report and draw the frame if not the first page.

        Args:
            args: varied amount of non-keyword arguments
            kwargs: varied amount of keyword arguments
        """
        super().add_page(*args, **kwargs)

        header_cursor_abscissa_position_in_mm: int = 35
        # Set the cursor at the top (e.g., 4 cm from the top).
        self.set_y(header_cursor_abscissa_position_in_mm)

    def _generate(self) -> None:
        """Generate a PDF questionnaire report."""
        self._draw_patient_name_rvh_and_barcode()
        self._draw_table_of_content()
        self._draw_questionnaire_result()

    def _draw_patient_name_rvh_and_barcode(self) -> None:  # noqa: WPS213
        """Generate a PDF questionnaire report."""
        patient_info = FPDFCellDictType(
            w=0,
            h=0,
            align='L',
            border=0,
            text=f'{self.patient_data.patient_first_name} {self.patient_data.patient_last_name}',
        )
        text_rvh = FPDFCellDictType(
            w=0,
            h=0,
            align='L',
            border=0,
            text=f'{self.patient_sites_and_mrns_str}',
        )

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=15)
        self.cell(**patient_info)
        self.code39(text='NO-SCAN', x=160, y=30, w=1, h=18)  # barcode generation
        self.ln(6)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=15)
        self.cell(**text_rvh)
        self.ln(8)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='', size=12)
        self.set_x(162)
        self.cell(
            text='*  NO  -  SCAN  *',
        )
        self.ln(2)

    def _set_report_metadata(self) -> None:
        """Set Questionnaire PDF's metadata.

        The following information is set:
            - Keywords associated with the report
            - Subject of the report
            - Title of the report
            - Producer of the document (e.g., the name of the software that generates the PDF)
        """
        self.set_keywords(
            'Questionnaire Report, '
            + 'Rapport des Questionnaire remplis et déclarés, '
            + 'Completed Questionnaire Report, '
            + 'Opal, '
            + 'Opal Health Informatics Group',
        )
        self.set_subject(f'Completed Questionnaire report for {self.patient_name}')
        self.set_title('Rapport des Questionnaire remplis et déclarés/Completed Questionnaire Report')
        self.set_producer(f'fpdf2 v{FPDF_VERSION}')

    def _draw_table_of_content(self) -> None:
        # Make an estimate to how many pages the TOC will take based on how many quesitonnaire are completed
        questionnaire_per_page1 = 15
        questionnaire_per_page = 17
        guesstimate = 0
        if len(QUESTIONNAIRE_DATA) <= questionnaire_per_page1:
            guesstimate = 1
        else:
            guesstimate = math.ceil(
                (len(QUESTIONNAIRE_DATA) - questionnaire_per_page1) / questionnaire_per_page,
            ) + 1
        self.insert_toc_placeholder(render_toc_with_table, guesstimate)

    def _draw_questionnaire_result(self) -> None:  # noqa: WPS213
        self.set_section_title_styles(
            # Level 0 titles:
            TitleStyle(
                font_family=QUESTIONNAIRE_REPORT_FONT,
                font_style='B',
                font_size_pt=15,
                color=None,
                underline=False,
                t_margin=-5,
                l_margin=None,
                b_margin=None,
            ),
            # Level 1 subtitles for questions:
            TitleStyle(
                font_family=QUESTIONNAIRE_REPORT_FONT,
                font_style='B',
                font_size_pt=1,
                color=(255, 255, 255),  # Font is white and size is 1 so we can hide it
                underline=False,
                t_margin=5,
                l_margin=0,
                b_margin=5,
            ),
            TitleStyle(
                font_family=QUESTIONNAIRE_REPORT_FONT,
                font_size_pt=14,
                color=128,
                underline=False,
                t_margin=20,
                l_margin=0,
                b_margin=10,
            ),
        )
        num = 0
        for title, last_updated in TABLE_DATA.values():  # noqa: WPS442
            # TODO: Add logic to print the multiple different questions, and graph associated with the questionnaires

            if num != 0:  # Skip empty first page
                self.add_page()
            self.set_font(QUESTIONNAIRE_REPORT_FONT, style='', size=16)
            self.start_section(f'{title}', level=1)  # For the TOC
            self.set_y(35)
            insert_paragraph(self, f'{title}', align=enums.Align.C)  # To print the title in the center
            self.ln(1)
            insert_paragraph(self, f'Dernière mise à jour: {last_updated}', align=enums.Align.C)
            self.ln(6)
            self.set_font(QUESTIONNAIRE_REPORT_FONT, size=12)
            insert_paragraph(self, 'TODO: add graphs', align=enums.Align.C)
            num += 1


class QuestionnaireReportService():
    """Service that provides functionality for generating questionnaire PDF reports."""

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

    def generate_questionnaire_report(
        self,
        institution_data: InstitutionData,
        patient_data: PatientData,
        site_data: SiteData,
        questionnaire_data: QuestionnaireData,
    ) -> Path:
        """Create a pathology PDF report.

        The generated report is saved in the directory specified in the QUESTIONNAIRE_REPORTS_PATH environment variable.

        Args:
            institution_data: institution data required to generate the PDF report
            patient_data: patient data required to generate the PDF report
            site_data: site data required to generate the PDF report
            questionnaire_data: questionnaire data required to generate the PDF report

        Returns:
            path to the generated pathology report
        """
        generated_at = timezone.localtime(timezone.now()).strftime('%Y-%b-%d_%H-%M-%S')
        report_file_name = '{first_name}_{last_name}_{date}_pathology'.format(
            first_name=patient_data.patient_first_name,
            last_name=patient_data.patient_last_name,
            date=generated_at,
        )
        # TODO: Change the report path and view to the questionnaire one's
        report_path = settings.PATHOLOGY_REPORTS_PATH / f'{report_file_name}.pdf'
        questionnaire_pdf = QuestionnairePDF(institution_data, patient_data, site_data, questionnaire_data)
        questionnaire_pdf.output(name=str(report_path))

        return report_path

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


def insert_toc_title(
    pdf: Any,
) -> None:
    """Insert the 'Table of contents' title and set fonts for the TOC.

    Args:
        pdf: The pdf
    """
    pdf.set_font(QUESTIONNAIRE_REPORT_FONT, size=16)
    pdf.underline = True
    pdf.set_x(12)
    insert_paragraph(pdf, 'Table of contents:')
    pdf.underline = False
    pdf.y += 5
    pdf.set_font(QUESTIONNAIRE_REPORT_FONT, size=12)
    pdf.x = 10


def render_toc_with_table(
    pdf: Any,
    outline: list[Any],
) -> None:
    """Render the table of content as a table .

    Args:
        pdf: The pdf
        outline: A list outline of the table of content
    """
    insert_toc_title(pdf)
    pdf.set_font_size(size=16)
    with pdf.table(
        borders_layout=enums.TableBordersLayout.NONE,
        text_align=(enums.Align.L, enums.Align.L, enums.Align.R),
        col_widths=(60, 30, 10),
    ) as table:
        table.row(TABLE_HEADER)
        for section in outline:
            if section.level < 2:
                data = TABLE_DATA[section.name]
                link = pdf.add_link(page=section.page_number)
                row = table.row()
                row.cell(data[0], link=link)
                row.cell(
                    f'{datetime.strptime(data[1],"%Y-%b-%d %H:%M",).strftime("%Y-%b-%d %H:%M")}',
                )
                row.cell(str(section.page_number), link=link)


def insert_paragraph(
    pdf: Any,
    text: Any,
    **kwargs: Any,
) -> None:
    """Insert the paragrah related to the questionnaires.

    Args:
        pdf: The pdf
        text: text to insert
        kwargs: varied amount of keyword arguments
    """
    pdf.multi_cell(
        w=pdf.epw,
        h=pdf.font_size,
        text=text,
        new_x='LMARGIN',
        new_y='NEXT',
        **kwargs,
    )
