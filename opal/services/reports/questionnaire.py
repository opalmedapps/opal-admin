"""Module providing business logic for generating questionnaire PDF reports using FPDF2."""
import io
import json
import logging
import math
import re
import types
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from django.conf import settings

import pandas as pd
import requests
from fpdf import FPDF, FPDF_VERSION, FontFace, FPDFException
from fpdf.enums import Align, TableBordersLayout
from fpdf.outline import OutlineSection
from plotly import express
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status

from opal.utils.base64_util import Base64Util

from .base import FPDFCellDictType, FPDFMultiCellDictType, InstitutionData, PatientData

if TYPE_CHECKING:
    from fpdf.fpdf import _Format, _Orientation  # noqa: WPS450


class QuestionType(Enum):
    """Question types and their IDs that are visualized in the questionnaire report."""

    CHECKBOX = 1  # noqa: WPS115
    NUMERIC = 2  # noqa: WPS115
    TEXT = 3  # noqa: WPS115
    RADIO = 4  # noqa: WPS115


class Question(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for generating a questionnaire PDF report.

    Attributes:
        question_text: name of the question title completed by the patient
        question_label: a short label describing the question
        question_type_id: the type or category ID of the question
        position: the order of the question within the questionnaire
        min_value: minimum allowed value for the answer (if applicable)
        max_value: maximum allowed value for the answer (if applicable)
        polarity: polarity value for the answer
        section_id: ID of the section
        answers: list of tuples representing timestamp and answer values
    """

    question_text: str
    question_label: str
    question_type_id: QuestionType
    position: int
    min_value: int | None
    max_value: int | None
    polarity: int
    section_id: int
    answers: list[tuple[datetime, str]]


class QuestionnaireData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for generating a questionnaire PDF report.

    Attributes:
        questionnaire_id: unique ID of the questionnaire
        questionnaire_title: name of questionnaire title completed by the patient
        last_updated: the date when the questionnaire was last updated by the patient
        questions: list of questions associated to the questionnaire

    """

    questionnaire_id: int
    questionnaire_title: str
    last_updated: datetime
    questions: list[Question]


FIRST_PAGE_NUMBER: int = 1
QUESTIONNAIRE_REPORT_FONT: str = 'Times'
AUTO_PAGE_BREAK_BOTTOM_MARGIN = 50

TABLE_HEADER = ('Questionnaires remplis', 'Dernière mise à jour', 'Page')
TEXT_QUESTIONS_TABLE_HEADER = ('Date', 'Response')


class QuestionnairePDF(FPDF):  # noqa: WPS214
    """Customized FPDF class that provides implementation for generating questionnaire PDF reports."""

    def __init__(
        self,
        institution_data: InstitutionData,
        patient_data: PatientData,
        questionnaire_data: list[QuestionnaireData],
        toc_pages: int | None = None,
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
            toc_pages: number of pages required to generate the toc
        """
        super().__init__()
        self.institution_data = institution_data
        self.questionnaire_data = questionnaire_data
        self.patient_name = f'{patient_data.patient_first_name} {patient_data.patient_last_name}'
        self.QUESTION_TYPE_HANDLERS = types.MappingProxyType(
            {
                QuestionType.TEXT: self._draw_text_answer_question,
                QuestionType.NUMERIC: self._draw_chart_for_numeric_question,
                QuestionType.RADIO: self._draw_text_answer_question,
                QuestionType.CHECKBOX: self._draw_text_answer_question,
            },
        )

        # Concatenated patient's site codes and MRNs for the header.
        sites_and_mrns_list = [
            f'{site_mrn["site_code"]}: {site_mrn["mrn"]}'
            for site_mrn in patient_data.patient_sites_and_mrns
        ]
        self.patient_sites_and_mrns_str = ', '.join(
            sites_and_mrns_list,
        )
        self.toc_pages = toc_pages if toc_pages is not None else self._calculate_toc_pages()
        self._set_report_metadata()
        self.set_auto_page_break(auto=True, margin=AUTO_PAGE_BREAK_BOTTOM_MARGIN)
        self.add_page()
        self._generate()

    def header(self) -> None:  # noqa: WPS213
        """Set the questionnaire PDF's header.

        This is automatically called by FPDF.add_page() and should not be called directly by the user application.
        """
        self.image(
            str(self.institution_data.institution_logo_path),
            x=5,
            y=5,
            w=60,
            h=12,
        )
        self.set_y(y=5)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='', size=15)
        patient_info = FPDFMultiCellDictType(
            w=0,
            h=None,
            align=Align.R,
            text=f'**{self.patient_name}**\n{self.patient_sites_and_mrns_str}',
        )
        self.multi_cell(**patient_info, markdown=True)
        self.ln(6)
        self.set_x(10)
        self.cell(
            **FPDFCellDictType(
                w=0,
                h=0,
                align=Align.L,
                border=0,
                text='Questionnaires remplis et déclarés par le patient',
                link='',
                markdown=False,
            ),
        )

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='U', size=10)
        self.set_text_color(0, 0, 255)
        self.set_x(155)
        self.cell(
            **FPDFCellDictType(
                w=0,
                h=0,
                align=Align.L,
                border=0,
                text='Retour à la Table des Matières',
                link=self.add_link(page=1),
                markdown=False,
            ),
        )

        self.line(10, 18, 200, 18)  # X1, Y1, X2, Y2

        self.line(10, 26, 200, 26)  # X1, Y1, X2, Y2

    def footer(self) -> None:
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
        # Move the cursor to the bottom (e.g., 3.5 cm from the bottom).
        self.set_y(y=-35)
        self.line(10, 260, 200, 260)
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='', size=12)
        self.cell(
            **FPDFCellDictType(
                w=0,
                h=5,
                text=f'**{self.institution_data.document_number}** '
                + f'Source: {self.institution_data.source_system}'
                + f'({datetime.now().strftime("%b %d, %Y")})',
                border=0,
                align=Align.L,
                link='',
                markdown=True,
            ),
        )
        self.cell(
            **FPDFCellDictType(
                w=5,
                h=5,
                text=f'Page {self.page_no()} de {{nb}}',
                border=0,
                align=Align.R,
                link='',
                markdown=False,
            ),
        )
        self.ln(10)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, size=9)
        self.multi_cell(**footer_block, markdown=True)

    def add_page(  # noqa: WPS211
        self,
        orientation: '_Orientation' = '',
        format_page: '_Format | tuple[float, float]' = '',
        same: bool = False,
        duration: int = 0,
        transition: Any | None = None,
    ) -> None:
        """Add new page to the questionnaire report and set the correct spacing for the header.

        Args:
            orientation: "portrait" or "landscape". Default to "portrait"
            format_page: "a3", "a4", "a5", "letter", "legal" or a tuple (width, height). Default to "a4"
            same: indicates to use the same page format as the previous page. Default to False
            duration: optional page’s display duration
            transition: optional visual transition to use when moving from another page
        """
        super().add_page(orientation, format_page, same, duration, transition)

        header_cursor_abscissa_position_in_mm: int = 35
        # Set the cursor at the top (e.g., 3.5 cm from the top).
        self.set_y(header_cursor_abscissa_position_in_mm)

    def _generate(self) -> None:
        """Generate a PDF questionnaire report."""
        self._draw_patient_name_site_and_barcode()
        self.insert_toc_placeholder(self._render_toc_with_table, self.toc_pages)
        self._draw_questionnaire_result()

    def _draw_patient_name_site_and_barcode(self) -> None:
        """Draw the patient's name, site information and barcode on the first page."""
        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='', size=15)
        patient_info = FPDFMultiCellDictType(
            w=0,
            h=None,
            align=Align.L,
            text=f'**{self.patient_name}**\n{self.patient_sites_and_mrns_str}',
        )
        self.multi_cell(**patient_info, markdown=True)
        self.code39(text='*NO-SCAN*', x=152, y=30, w=1, h=18)
        self.ln(4)

        self.set_font(family=QUESTIONNAIRE_REPORT_FONT, style='', size=12)
        self.set_x(160)
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

    def _calculate_toc_pages(self) -> int:
        # Estimate how many pages the TOC will require based on the number of completed questionnaires.
        first_page_count = 14
        subsequent_page_count = 17
        total_questionnaires = len(self.questionnaire_data)
        if total_questionnaires <= first_page_count:
            return 1
        return math.ceil((total_questionnaires - first_page_count) / subsequent_page_count) + 1

    def _draw_questionnaire_result(self) -> None:
        for index, data in enumerate(self.questionnaire_data):

            if index > 0:  # Skip empty first page
                self.add_page()
            self.set_font(QUESTIONNAIRE_REPORT_FONT, style='B', size=16)
            self.start_section(data.questionnaire_title)  # create new section for table of contents
            # Display the questionnaire title and the most recent questionnaire date, centered at the top of the page.
            self._insert_paragraph(data.questionnaire_title, align=Align.C)
            self.ln(1)
            self._insert_paragraph(
                f'Dernière mise à jour: {data.last_updated.strftime("%b %d, %Y %H:%M")}',
                align=Align.C,
            )
            self.ln(6)
            self.set_font(QUESTIONNAIRE_REPORT_FONT, size=12)
            self._draw_questions_results(data.questions)

    def _draw_questions_results(self, questions: list[Question]) -> None:
        """Display question based on its type.

        Args:
            questions: list of questions associated with the questionnaire
        """
        for question in questions:
            question_type = QuestionType(question.question_type_id)
            handler = self.QUESTION_TYPE_HANDLERS.get(question_type, self._draw_text_answer_question)
            handler(question)

    def _prepare_question_chart(self, question: Question) -> pd.DataFrame:
        """Prepare the question for the chart.

        Args:
            question: question that needs to be prepared

        Returns:
            DataFrame of the question's answer values
        """
        if self.will_page_break(50):  # Ensure the title and chart are on the same page
            self.add_page()
        self.set_font(QUESTIONNAIRE_REPORT_FONT, style='', size=14)
        self.multi_cell(
            w=self.epw,
            h=self.font_size,
            text=f'{question.question_text}',
            new_x='LMARGIN',
            new_y='NEXT',
            align=Align.L,
        )
        self.ln(5)
        x_data = []
        y_data = []
        for answers in question.answers:
            x_data.append(answers[0])
            y_data.append(int(answers[1]))

        return pd.DataFrame(
            {
                'Last Updated': x_data,
                'Value': y_data,
            },
        )

    def _draw_chart_for_numeric_question(self, question: Question) -> None:
        """Generate a chart for a numeric question (e.g., `SLIDER`) type.

        Args:
            question: numeric question to be visualized in a chart
        """
        data_frame = self._prepare_question_chart(question)

        chart_trace = express.line(
            data_frame,
            x=data_frame.iloc[:, 0],
            y=data_frame.iloc[:, 1],
            markers=True,
            width=810,
            height=310,
            text='Value',
            template='plotly_white',
        )
        chart_trace.update_traces(
            textposition='top center',
            marker={'size': 10},
            textfont={'size': 15, 'weight': 'bold'},
        )

        chart_trace.update_yaxes(
            showgrid=True,
        )
        # Make sure we see the max and the min value of the markers
        if question.max_value and question.min_value is not None:
            chart_trace.for_each_yaxis(
                lambda var: var.update({'range': [
                    0, question.max_value * 1.1,
                ],
                }),
            )
        chart_trace.update_layout(
            yaxis_title=question.question_label,
            xaxis_title=None,
            margin={
                'l': 40,
                'r': 40,
                't': 0,
                'b': 0,
            },
            height=310,  # Keep height fixed
            xaxis={
                'tickangle': 20,  # Better readability than flat
            },
        )

        image = io.BytesIO(chart_trace.to_image(format='PNG', engine='kaleido'))
        self.image(image, w=self.epw, x=Align.R)
        self.ln(10)

    def _draw_text_answer_question(self, question: Question) -> None:  # noqa: WPS213
        """Draw the table for text answer question.

        Args:
            question: text answer question to be displayed in a table
        """
        if self.will_page_break(30):  # Ensure the title and chart are on the same page
            self.add_page()
        self.set_font(QUESTIONNAIRE_REPORT_FONT, style='', size=14)
        self.multi_cell(
            w=self.epw,
            h=self.font_size,
            text=f'{question.question_text}',
            new_x='LMARGIN',
            new_y='NEXT',
            align=Align.L,
        )
        self.ln(4)

        self.set_font(QUESTIONNAIRE_REPORT_FONT, size=12)
        headings_style = FontFace(fill_color=(160, 207, 236), emphasis='BOLD')
        with self.table(
            borders_layout=TableBordersLayout.ALL,
            text_align=(Align.L, Align.L),
            col_widths=(30, 60),
            headings_style=headings_style,
        ) as table:
            table.row(TEXT_QUESTIONS_TABLE_HEADER)
            for answers in reversed(question.answers):
                row = table.row()
                row.cell(
                    f'{answers[0].strftime("%b %d, %Y %H:%M")}',
                )
                row.cell(
                    f'{answers[1]}',
                )
        self.ln(10)

    def _insert_toc_title(
        self,
    ) -> None:
        """Insert the 'Table of contents' title and set fonts for the TOC."""
        self.set_font(QUESTIONNAIRE_REPORT_FONT, style='', size=30)
        self.set_x(10)
        self._insert_paragraph('Table des matières:', align=Align.L)
        self.set_y(self.y + 5)
        self.set_font(QUESTIONNAIRE_REPORT_FONT, size=12)
        self.set_x(10)

    def _render_toc_with_table(  # noqa: WPS210
        self,
        pdf: FPDF,
        outline: list[OutlineSection],
    ) -> None:
        """Render the table of content as a table .

        Args:
            pdf: The FPDF instance
            outline: A list outline of the table of content
        """
        self._insert_toc_title()
        pdf.set_font_size(size=16)
        with self.table(
            borders_layout=TableBordersLayout.NONE,
            text_align=(Align.L, Align.L, Align.R),
            col_widths=(60, 30, 10),
        ) as table:
            table.row(TABLE_HEADER)
            for idx, section in enumerate(outline):
                questionnaire = self.questionnaire_data[idx]
                link = pdf.add_link(page=section.page_number)
                row = table.row()
                row.cell(
                    questionnaire.questionnaire_title,
                    style=FontFace(emphasis='UNDERLINE', color=(0, 0, 255)),
                    link=link,
                )
                row.cell(
                    questionnaire.last_updated.strftime('%b %d, %Y %H:%M'),
                )
                row.cell(str(section.page_number), link=link)

    def _insert_paragraph(
        self,
        text: str,
        align: str | Align,
    ) -> None:
        """Insert the paragraph related to the questionnaires.

        Args:
            text: text to insert
            align: desired alignement of the paragraph
        """
        self.multi_cell(
            w=self.epw,
            h=self.font_size,
            text=text,
            new_x='LMARGIN',
            new_y='NEXT',
            align=align,
        )


def generate_pdf(
    institution: InstitutionData,
    patient: PatientData,
    questionnaires: list[QuestionnaireData],
) -> bytearray:
    """Create a questionnaire PDF report.

    Args:
        institution: institution data required to generate the PDF report
        patient: patient data required to generate the PDF report
        questionnaires: questionnaire list required to generate the PDF report

    Returns:
        output of the generated questionnaire report after checking if the number
        of pages required for the toc is correct so it can export without errors

    Raises:
        FPDFException: If any other errors occurs during the PDF generation
    """
    try:
        result = _generate_pdf(institution, patient, questionnaires)
    except FPDFException as exc:
        error = str(exc)
        if 'ToC ended on page' in error:
            match = re.search(r'ToC ended on page (\d+) while it was expected to span exactly (\d+) pages', error)
            if match:
                actual_pages = int(match.group(1))
                return _generate_pdf(institution, patient, questionnaires, actual_pages)
        raise exc

    return result


def _generate_pdf(
    institution: InstitutionData,
    patient: PatientData,
    questionnaires: list[QuestionnaireData],
    toc_pages: int | None = None,
) -> bytearray:
    """Create a questionnaire PDF report.

    Args:
        institution: institution data required to generate the PDF report
        patient: patient data required to generate the PDF report
        questionnaires: questionnaire list required to generate the PDF report
        toc_pages: number of pages required to generate the toc

    Returns:
        output of the generated questionnaire report
    """
    pdf = QuestionnairePDF(institution, patient, questionnaires, toc_pages=toc_pages)

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
