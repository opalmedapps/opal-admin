"""Module providing business logic for generating questionnaire PDF reports using FPDF2."""
import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple

from django.conf import settings

import requests
from fpdf import FPDF, FPDF_VERSION, FontFace, TitleStyle
from fpdf.enums import Align, TableBordersLayout
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status

from opal.utils.base64_util import Base64Util

from .base import FPDFCellDictType, FPDFMultiCellDictType, InstitutionData, PatientData

# TODO: Correctly define the questionnaireData with it's appropriate attributes


class QuestionnaireData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for generating a questionnaire PDF report.

    Attributes:
        title: list of questionnaire title completed by the patient
        updated_at: the date when the questionnaire was last updated by the patient
    """

    questionnaire_title: str
    updated_at: datetime


temporary_data = [
    QuestionnaireData(
        questionnaire_title='Temporary',
        updated_at=datetime(2024, 10, 21, 14, 0),
    ),
]

FIRST_PAGE_NUMBER: int = 1
QUESTIONNAIRE_REPORT_FONT: str = 'Times'
AUTO_PAGE_BREAK_BOTTOM_MARGIN = 50

TABLE_HEADER = ('Questionnaires remplis', 'Dernière mise à jour', 'Page')


class QuestionnairePDF(FPDF):  # noqa: WPS214
    """Customized FPDF class that provides implementation for generating questionnaire PDF reports."""

    def __init__(
        self,
        institution_data: InstitutionData,
        patient_data: PatientData,
        questionnaire_data: list[QuestionnaireData],
    ) -> None:
        """Initialize a `QuestionnairePDF` instance for generating questionnaire reports.

        The initialization consists of 3 steps:
            - Initialization of the `FPDF` instance
            - Setting the PDF's metadata (e.g., author, creation date, keywords, etc.)
            - Generating the PDF by using FPDF's templates

        Args:
            institution_data: institution data required to generate the PDF report
            patient_data: patient data required to generate the PDF report
            questionnaire_data: questionnaire data required to generate the PDF report
        """
        super().__init__()
        self.institution_data = institution_data
        self.questionnaire_data = questionnaire_data
        self.patient_name = f'{patient_data.patient_first_name} {patient_data.patient_last_name}'
        # Concatenated patient's site codes and MRNs for the header.
        sites_and_mrns_list = [
            f'{site_mrn["site_code"]}: {site_mrn["mrn"]}'
            for site_mrn in patient_data.patient_sites_and_mrns
        ]
        self.patient_sites_and_mrns_str = ', '.join(
            sites_and_mrns_list,
        )
        self._set_report_metadata()
        self.set_auto_page_break(auto=True, margin=AUTO_PAGE_BREAK_BOTTOM_MARGIN)
        self.add_page()
        self._generate()

    def header(self) -> None:  # noqa: WPS213
        """Set the questionnaire PDF's header.

        This is automatically called by FPDF.add_page() and should not be called directly by the user application.
        """
        header_patient_info = FPDFCellDictType(
            w=0,
            h=0,
            align=Align.R,
            border=0,
            text=f'{self.patient_name}',
        )
        header_text = FPDFCellDictType(
            w=0,
            h=0,
            align=Align.R,
            border=0,
            text=f'{self.patient_sites_and_mrns_str}',
        )
        header_title = FPDFCellDictType(
            w=0,
            h=0,
            align=Align.L,
            border=0,
            text='Questionnaires remplis et déclarés par le patient',
        )
        header_toc_link = FPDFCellDictType(
            w=0,
            h=0,
            align=Align.L,
            border=0,
            text='Retour à la Table des Matières',
        )
        self.image(
            str(self.institution_data.institution_logo_path),
            x=5,
            y=5,
            w=60,
            h=12,
        )
        self.set_y(y=5)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=15)
        self.cell(**header_patient_info)
        self.ln(6)

        self.cell(70)
        self.cell(**header_text)

        self.ln(11)
        self.cell(8)
        self.set_x(10)
        self.cell(**header_title)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='U', size=10)
        self.set_text_color(0, 0, 255)
        self.set_x(160)
        self.cell(**header_toc_link, link=str(self.add_link(page=1)))

        self.line(10, 18, 200, 18)  # X1, Y1, X2, Y2

        self.line(10, 26, 200, 26)  # X1, Y1, X2, Y2

    def footer(self) -> None:  # noqa: WPS213
        """Set the questionnaire PDF's footer.

        This is automatically called by FPDF.add_page() and FPDF.output().

        It should not be called directly by the user application.
        """
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
            align=Align.R,
        )
        source_date = FPDFCellDictType(
            w=0,
            h=5,
            text='Tempory text',
            border=0,
            align=Align.L,
        )
        self.set_y(y=-35)
        # Move the cursor to the bottom (e.g., 3.5 cm from the bottom).
        self.line(10, 260, 200, 260)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=12)
        self.cell(**source_date)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='', size=12)
        self.cell(**footer_page)
        self.ln(10)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, size=9)
        self.multi_cell(**footer_block, markdown=True)

    def add_page(self, *args: Any, **kwargs: Any) -> None:
        """Add new page to the questionnaire report and set the correct spacing for the header.

        Args:
            args: varied amount of non-keyword arguments
            kwargs: varied amount of keyword arguments
        """
        super().add_page(*args, **kwargs)

        header_cursor_abscissa_position_in_mm: int = 35
        # Set the cursor at the top (e.g., 3.5 cm from the top).
        self.set_y(header_cursor_abscissa_position_in_mm)

    def _generate(self) -> None:
        """Generate a PDF questionnaire report."""
        self._draw_patient_name_site_and_barcode()
        self._draw_table_of_content()
        self._draw_questionnaire_result()

    def _draw_patient_name_site_and_barcode(self) -> None:  # noqa: WPS213
        """Draw the patient's name, site information and barcode on the first page."""
        patient_info = FPDFCellDictType(
            w=0,
            h=0,
            align=Align.L,
            border=0,
            text=f'{self.patient_name}',
        )
        patient_site_and_mrns = FPDFCellDictType(
            w=0,
            h=0,
            align=Align.L,
            border=0,
            text=f'{self.patient_sites_and_mrns_str}',
        )

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='B', size=15)
        self.cell(**patient_info)
        self.code39(text='NO-SCAN', x=160, y=30, w=1, h=18)  # barcode generation
        self.ln(6)
        self.cell(**patient_site_and_mrns)
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
        # Make an estimate to how many pages the TOC will take based on how many questionnaire are completed
        first_page_count = 15
        subsequent_page_count = 17
        total_questions = len(QuestionnaireData.questionnaire_title)

        guesstimate = 0
        if total_questions <= first_page_count:
            guesstimate = 1
        else:
            guesstimate = math.ceil((total_questions - first_page_count) / subsequent_page_count) + 1
        self.insert_toc_placeholder(self._render_toc_with_table, guesstimate)

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
        for data in temporary_data:  # noqa: WPS442
            # TODO: Add logic to print the multiple different questions, and graph associated with the questionnaires

            if num != 0:  # Skip empty first page
                self.add_page()
            self.set_font(QUESTIONNAIRE_REPORT_FONT, style='', size=16)
            self.start_section(data.questionnaire_title, level=1)  # For the TOC
            self.set_y(35)
            self._insert_paragraph(self, data.questionnaire_title, align=Align.C)  # To print the title in the center
            self.ln(1)
            self._insert_paragraph(self, f'Dernière mise à jour: {data.updated_at}', align=Align.C)
            self.ln(6)
            self.set_font(QUESTIONNAIRE_REPORT_FONT, size=12)
            self._insert_paragraph(self, 'TODO: add graphs', align=Align.C)
            num += 1

    def _insert_toc_title(
        self,
        pdf: FPDF,
    ) -> None:
        """Insert the 'Table of contents' title and set fonts for the TOC.

        Args:
            pdf: The pdf
        """
        pdf.set_font(QUESTIONNAIRE_REPORT_FONT, size=20)
        pdf.set_x(12)
        self._insert_paragraph(self, 'Table des matières:')
        pdf.y += 5  # noqa: WPS111
        pdf.set_font(QUESTIONNAIRE_REPORT_FONT, size=12)
        pdf.x = 10  # noqa: WPS111

    def _render_toc_with_table(  # noqa: WPS210
        self,
        pdf: Any,
        outline: list[Any],
    ) -> None:
        """Render the table of content as a table .

        Args:
            pdf: the pdf
            outline: A list outline of the table of content
        """
        self._insert_toc_title(pdf)
        pdf.set_font_size(size=16)
        with self.table(
            borders_layout=TableBordersLayout.NONE,
            text_align=(Align.L, Align.L, Align.R),
            col_widths=(60, 30, 10),
        ) as table:
            table.row(TABLE_HEADER)
            for idx, section in enumerate(outline):
                if section.level < 2:
                    data = temporary_data[idx]
                    link = pdf.add_link(page=section.page_number)
                    row = table.row()
                    row.cell(
                        data.questionnaire_title,
                        style=FontFace(emphasis='UNDERLINE', color=(0, 0, 255)),
                        link=link,
                    )
                    row.cell(
                        data.updated_at.strftime('%Y-%b-%d %H:%M'),
                    )
                    row.cell(str(section.page_number), link=link)

    def _insert_paragraph(
        self,
        pdf: Any,
        text: Any,
        **kwargs: Any,
    ) -> None:
        """Insert the paragraph related to the questionnaires.

        Args:
            pdf: the pdf
            text: text to insert
            kwargs: varied amount of keyword arguments
        """
        self.multi_cell(
            w=pdf.epw,
            h=pdf.font_size,
            text=text,
            new_x='LMARGIN',
            new_y='NEXT',
            **kwargs,
        )


def generate_pdf(
    institution_data: InstitutionData,
    patient_data: PatientData,
    questionnaire_data: list[QuestionnaireData],
) -> bytearray:
    """Create a questionnaire PDF report.

    Args:
        institution_data: institution data required to generate the PDF report
        patient_data: patient data required to generate the PDF report
        questionnaire_data: questionnaire data required to generate the PDF report

    Returns:
        output of the generated questionnaire report
    """
    pdf = QuestionnairePDF(institution_data, patient_data, questionnaire_data)

    return pdf.output()


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
