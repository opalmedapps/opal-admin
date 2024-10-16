"""Module providing business logic for generating questionnaire PDF reports using FPDF2."""

import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, NamedTuple

from fpdf import FPDF, FPDF_VERSION, FontFace, TitleStyle
from fpdf.enums import Align, TableBordersLayout
from typing_extensions import TypedDict


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


class InstitutionData(NamedTuple):
    """Information about an institution from which a report was received.

    Attributes:
        institution_logo_path: file path of the instituion's logo image
    """

    institution_logo_path: Path


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
        title: list of questionnaire title completed by the patient
        updated_at: the date when the questionnaire was last updated by the patient
    """

    quetionnaire_title: list[str]
    updated_at: list[str]


FIRST_PAGE_NUMBER: int = 1
QUESTIONNAIRE_REPORT_FONT: str = 'Times'

# TODO: Add query for all the the completed questionnaire data of the patient
questionnaire_data_info = QuestionnaireData(
    quetionnaire_title=[],
    updated_at=[],
)

# Subject to changes once the data is correctly imported
sorted_data = sorted(
    zip(questionnaire_data_info.quetionnaire_title, questionnaire_data_info.updated_at),
    key=lambda sort: datetime.strptime(sort[1], '%Y-%m-%d %H:%M'),
    reverse=True,
)

TABLE_DATA = {}  # noqa: WPS407

for title, update_date in sorted_data:
    last_updated = datetime.strptime(update_date, '%Y-%m-%d %H:%M')
    formatted_date = last_updated.strftime('%Y-%b-%d %H:%M')
    TABLE_DATA[title] = (title, formatted_date)


TABLE_HEADER = ('Questionnaires remplis', 'Dernière mise à jour', 'Page')


class QuestionnairePDF(FPDF):  # noqa: WPS214, WPS230
    """Customized FPDF class that provides implementation for generating questionnaire PDF reports."""

    def __init__(
        self,
        institution_data: InstitutionData,
        patient_data: PatientData,
        questionnaire_data: QuestionnaireData,
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
        self.patient_data = patient_data
        self.questionnaire_data = questionnaire_data
        self.patient_name = f'{patient_data.patient_last_name}, {patient_data.patient_first_name}'.upper()
        # Concatenated patient's site codes and MRNs for the header.
        sites_and_mrns_list = [
            f'{site_mrn["site_code"]}: {site_mrn["mrn"]}'
            for site_mrn in self.patient_data.patient_sites_and_mrns
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
            align=Align.R,
            border=0,
            text=f'{self.patient_data.patient_first_name} {self.patient_data.patient_last_name}',
        )
        header_text_rvh = FPDFCellDictType(
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
            align=Align.R,
        )
        footer_fmu_date = FPDFCellDictType(
            w=0,
            h=5,
            text='Tempory text',
            border=0,
            align=Align.L,
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
        """Add new page to the questionnaire report and set the correct spacing for the header.

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
        self._draw_patient_name_site_and_barcode()
        self._draw_table_of_content()
        self._draw_questionnaire_result()

    def _draw_patient_name_site_and_barcode(self) -> None:  # noqa: WPS213
        """Draw the patients name, site information and barcode on the first page."""
        patient_info = FPDFCellDictType(
            w=0,
            h=0,
            align=Align.L,
            border=0,
            text=f'{self.patient_data.patient_first_name} {self.patient_data.patient_last_name}',
        )
        text_rvh = FPDFCellDictType(
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
        if len(questionnaire_data_info.quetionnaire_title) <= questionnaire_per_page1:
            guesstimate = 1
        else:
            guesstimate = math.ceil(
                (len(questionnaire_data_info.quetionnaire_title) - questionnaire_per_page1) / questionnaire_per_page,
            ) + 1
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
        for title, last_updated in TABLE_DATA.values():  # noqa: WPS442
            # TODO: Add logic to print the multiple different questions, and graph associated with the questionnaires

            if num != 0:  # Skip empty first page
                self.add_page()
            self.set_font(QUESTIONNAIRE_REPORT_FONT, style='', size=16)
            self.start_section(title, level=1)  # For the TOC
            self.set_y(35)
            self._insert_paragraph(self, title, align=Align.C)  # To print the title in the center
            self.ln(1)
            self._insert_paragraph(self, f'Dernière mise à jour: {last_updated}', align=Align.C)
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

    def _render_toc_with_table(
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
            for section in outline:
                if section.level < 2:
                    data = TABLE_DATA[section.name]
                    link = pdf.add_link(page=section.page_number)
                    row = table.row()
                    row.cell(
                        data[0],
                        style=FontFace(emphasis='UNDERLINE', color=(0, 0, 255)),
                        link=link,
                    )
                    row.cell(
                        f'{datetime.strptime(data[1],"%Y-%b-%d %H:%M",).strftime("%Y-%b-%d %H:%M")}',
                    )
                    row.cell(str(section.page_number), link=link)

    def _insert_paragraph(
        self,
        pdf: Any,
        text: Any,
        **kwargs: Any,
    ) -> None:
        """Insert the paragrah related to the questionnaires.

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
