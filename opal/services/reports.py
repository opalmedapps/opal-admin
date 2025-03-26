"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import json
import logging
import math
import textwrap
from datetime import date, datetime
from pathlib import Path
from typing import Any, NamedTuple, Optional

from django.conf import settings
from django.utils import timezone

import requests
from fpdf import FPDF, FPDF_VERSION, Align, FlexTemplate
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status
from typing_extensions import Literal, TypedDict

from opal.utils.base64 import Base64Util

FPDFCellDictType = TypedDict(
    'FPDFCellDictType',
    {
        'w': Optional[float],
        'h': Optional[float],
        'text': str,
        'border': bool | str | Literal[0, 1],
        'align': str | Align,
    },
)

FPDFMultiCellDictType = TypedDict(
    'FPDFMultiCellDictType',
    {
        'w': float,
        'h': Optional[float],
        'text': str,
        'align': str | Align,
    },
)

FPDFFontDictType = TypedDict(
    'FPDFFontDictType',
    {
        'family': Optional[str],
        'style': Literal[
            '',
            'B',
            'I',
            'U',
            'BU',
            'UB',
            'BI',
            'IB',
            'IU',
            'UI',
            'BIU',
            'BUI',
            'IBU',
            'IUB',
            'UBI',
            'UIB',
        ],
        'size': int,
    },
)

FPDFRectDictType = TypedDict(
    'FPDFRectDictType',
    {
        'x': float,
        'y': float,
        'w': float,
        'h': float,
        'style': Optional[str],
    },
)


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
        site_postal_code: the postal code that specified in the address (e.g., H4A3J1)
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


FIRST_PAGE_NUMBER: int = 1
PATHOLOGY_REPORT_FONT: str = 'helvetica'


class PathologyPDF(FPDF):  # noqa: WPS214
    """Customized FPDF class that provides implementation for generating pathology PDF reports."""

    def __init__(
        self,
        pathology_data: PathologyData,
    ) -> None:
        """Initialize a `PathologyPDF` instance for generating pathology reports.

        The initialization consists of 3 steps:
            - Initialization of the `FPDF` instance
            - Setting the PDF's metadata (e.g., author, creation date, keywords, etc.)
            - Generating the PDF by using FPDF's templates

        Args:
            pathology_data: pathology data required to generate the PDF report
        """
        super().__init__()
        self.pathology_data = pathology_data
        self.patient_name = f'{pathology_data.patient_last_name}, {pathology_data.patient_first_name}'.upper()
        # Concatenated patient's site codes and MRNs for the header.
        sites_and_mrns_list = [
            f'{site_mrn["site_code"]}-{site_mrn["mrn"]}' for site_mrn in self.pathology_data.patient_sites_and_mrns
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
        """Set the pathology PDF's header.

        This is automatically called by FPDF.add_page() and should not be called directly by the user application.
        """
        if self.page != FIRST_PAGE_NUMBER:
            header_text_fr = FPDFCellDictType(
                w=0,
                h=None,
                align='L',
                border=0,
                text='Pathologie Chirurgicale Rapport (suite)',
            )
            header_text_en = FPDFCellDictType(
                w=0,
                h=None,
                align='L',
                border=0,
                text='Surgical Pathology Final Report (continuation)',
            )
            header_patient_info = FPDFCellDictType(
                w=0,
                h=None,
                align='L',
                border=0,
                text=f'Patient : {self.patient_name} [{self.patient_sites_and_mrns_str}]',
            )

            self.set_font(family=PATHOLOGY_REPORT_FONT, style='B', size=10)
            self.cell(4)
            self.cell(**header_text_fr)
            self.ln(4)

            self.set_font(family=PATHOLOGY_REPORT_FONT, size=10)
            self.cell(4)
            self.cell(**header_text_en)
            self.ln(7)

            self.set_font(family=PATHOLOGY_REPORT_FONT, style='B', size=10)
            self.cell(4)
            self.cell(**header_patient_info)

    def footer(self) -> None:
        """Set the pathology PDF's footer.

        This is automatically called by FPDF.add_page() and FPDF.output().

        It should not be called directly by the user application.
        """
        # Move the cursor to the bottom (e.g., 4 cm from the bottom).
        footer_text: str = (
            "Ce rapport a été généré par Opal à partir des données du système RIS de l'hôpital. "
            + "Les données ne sont pas traduites et sont partagées avec vous telles qu'elles sont stockées dans "
            + "le système de l'hôpital. Elles sont destinées à l'information des patients et non à un usage clinique.\n"
            + "This report was generated by Opal from the hospital's RIS system data. This data is not translated, and "
            + "is being shared with you as it is stored in the hospital's system. For patient information, not for "
            + 'clinical use.'
        )
        footer_cursor_abscissa_position_in_mm: int = -40
        footer_block = FPDFMultiCellDictType(w=180, h=None, align='L', text=footer_text)
        footer_page = FPDFCellDictType(
            w=0,
            h=10,
            text=f'Page {self.page_no()}/{{nb}}',
            border=0,
            align='R',
        )
        self.set_y(y=footer_cursor_abscissa_position_in_mm)
        self.set_font(family=PATHOLOGY_REPORT_FONT, size=9)
        self.cell(4)
        self.multi_cell(**footer_block)
        self.ln(5)

        # Print page number:
        self.set_font(family=PATHOLOGY_REPORT_FONT, style='B', size=9)
        self.cell(**footer_page)

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

    def _draw_other_pages_frame(self, height_of_section: int) -> None:
        """Draw the pathology section frame for the pages except the first page.

        Args:
            height_of_section: the height of the section to be added
        """
        frame_size = FPDFRectDictType(
            x=15,
            y=30,
            w=180,
            h=self.get_y() - height_of_section if self.get_y() > height_of_section else 0,
            style='D',
        )
        self.rect(**frame_size)

    def _generate(self) -> None:
        """Generate a PDF pathology report."""
        self._draw_site_logo()
        self._draw_site_address_and_patient_table()
        self._draw_pathology_table_title()
        self._draw_pathology_table_frame()
        self._draw_report_number_and_date_table()
        self._draw_pathology_table_sections()
        self._add_new_page_if_needed()
        self._draw_report_prepared_by()

    def _set_report_metadata(self) -> None:
        """Set pathology PDF's metadata.

        The following information is set:
            - Keywords associated with the report
            - Subject of the report
            - Title of the report
            - Producer of the document (e.g., the name of the software that generates the PDF)
        """
        self.set_keywords((
            'Pathology Report, '
            + 'Pathologie Chirurgicale Rapport Final, '
            + 'Surgical Pathology Final Report, '
            + 'Opal, '
            + 'Opal Health Informatics Group'
        ))
        self.set_subject(f'Pathology report for {self.patient_name}')
        self.set_title('Pathologie Chirurgicale Rapport Final/Surgical Pathology Final Report')
        self.set_producer('fpdf2 v{0}'.format(FPDF_VERSION))

    def _draw_site_logo(self) -> None:
        """Draw the site logo that is shown at the top of the first page."""
        self.image(
            str(self.pathology_data.site_logo_path),
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

    def _draw_pathology_table_title(self) -> None:
        """Draw pathology table title."""
        table_title_font = FPDFFontDictType(
            family=PATHOLOGY_REPORT_FONT,
            style='B',
            size=12,
        )
        title_fr = FPDFCellDictType(w=0, h=10, align='C', border=0, text='PATHOLOGIE CHIRURGICALE RAPORT FINAL')
        title_en = FPDFCellDictType(w=0, h=10, align='C', border=0, text='SURGICAL PATHOLOGY FINAL REPORT')
        space_between_titles: int = 6  # the height between titles
        title_indentation: int = 12    # to make an indentation from previous section/block

        self.set_font(**table_title_font)
        self.ln(title_indentation)
        self.cell(**title_fr)
        self.ln(space_between_titles)
        self.cell(**title_en)

    def _draw_pathology_table_frame(self) -> None:
        """Draw pathology table."""
        # Grey area at the top of the table.
        grey_area_color = {'r': 211, 'g': 211, 'b': 211}
        self.set_fill_color(**grey_area_color)
        grey_area_dimension = FPDFRectDictType(
            x=15,
            y=self.get_y() + 10,
            w=180,
            h=5,
            style='DF',
        )
        self.rect(**grey_area_dimension)

        # Draw the pathology table frame for the first page.
        page_height_in_mm: int = 297
        table_length_offset: int = 55
        first_page_frame = FPDFRectDictType(
            x=15,
            y=self.get_y() + 10,
            w=180,
            h=page_height_in_mm - (self.get_y() + table_length_offset),
            style='D',
        )
        self.rect(**first_page_frame)

    def _draw_report_number_and_date_table(self) -> None:
        """Draw report number and date table."""
        report_number_and_date_table = FlexTemplate(self, self._get_report_number_and_date_table())
        report_number_and_date_table.render()

    def _draw_pathology_table_sections(self) -> None:
        """Define and iterate through the pathology sections that need to be drawn."""
        pathology_sections = [
            {'section_title': 'CLINICAL INFORMATION', 'section_content': self.pathology_data.observation_clinical_info},
            {'section_title': 'SPECIMEN', 'section_content': self.pathology_data.observation_specimens},
            {'section_title': 'GROSS DESCRIPTION', 'section_content': self.pathology_data.observation_descriptions},
            {'section_title': 'DIAGNOSIS', 'section_content': self.pathology_data.observation_diagnosis},
        ]
        block_top_indentation: int = 5      # to make an indentation from previous section/block
        block_bottom_indentation: int = 20  # to make an indentation at the end of the section

        self.ln(block_top_indentation)
        for section in pathology_sections:
            self._draw_pathology_section(**section)  # type: ignore[arg-type]

        self.ln(block_bottom_indentation)

    def _draw_pathology_section(
        self,
        section_title: str,
        section_content: list[str],
    ) -> None:
        """Draw pathology table section.

        Args:
            section_title: the title of the section
            section_content: the text content of the section
        """
        section_title_font = FPDFFontDictType(
            family=PATHOLOGY_REPORT_FONT,
            style='B',
            size=12,
        )
        section_content_font = FPDFFontDictType(
            family=PATHOLOGY_REPORT_FONT,
            style='',
            size=12,
        )
        new_abscissa_position: int = 20
        section_title_block = FPDFCellDictType(w=0, h=10, border=0, align='L', text=section_title)
        section_content_block = FPDFMultiCellDictType(
            w=155,
            h=None,
            align='J',
            text='\n\n\n\n'.join(section_content),
        )

        self.set_font(**section_title_font)
        self.ln(10)
        self.set_x(new_abscissa_position)
        self.cell(**section_title_block)
        self.ln(10)
        self.set_x(new_abscissa_position)
        self.set_font(**section_content_font)
        self.multi_cell(**section_content_block)

    def _add_new_page_if_needed(self) -> None:
        """Add new page if the prepared-by-table will not fit the current page."""
        height_of_section: int = 40      # the height of the section to be added
        new_ordinate_position: int = 30  # the position of the ordinate on the new page
        if self.will_page_break(height_of_section):
            self.add_page()
            self.set_y(new_ordinate_position)
        self._draw_other_pages_frame(height_of_section)

    def _draw_report_prepared_by(self) -> None:
        """Draw the "report prepared by" table."""
        report_prepared_by_template = FlexTemplate(
            self,
            self._get_report_prepared_by_table(),
        )
        report_prepared_by_template.render()

    def _get_site_address_patient_info_box(self) -> list[dict[str, Any]]:   # noqa: WPS210
        """Build a table/box that is shown at the top of the first page.

        The table contains site's and patient's information.

        Returns:
            dictionary containing data needed to build a table that is shown at the top of the first page.
        """
        sites_and_mrns = self.pathology_data.patient_sites_and_mrns
        mrns_and_sites_multiline = '\n'.join(
            [f'{site_mrn["site_code"]}# : {site_mrn["mrn"]}' for site_mrn in sites_and_mrns],
        )
        site_city = (
            f'{self.pathology_data.site_city} '
            + f'({self.pathology_data.site_province}) '
            + f'{self.pathology_data.site_postal_code}'
        ) if str(self.pathology_data.site_city) else ''
        site_phone = (
            f'Tél. : {self.pathology_data.site_phone}'
        ) if str(self.pathology_data.site_phone) else ''

        # Wrap the text with the maximum characters can be filled in each line.
        wrapper = textwrap.TextWrapper(
            width=int((190 - 108) / 2) - 1,
        )
        patient_name = wrapper.fill(text=f'Nom/Name: {self.patient_name}')
        # Calculate the number of the linse patient name will occupy
        line = math.ceil(len(patient_name) * 2 / (190 - 108))
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
                'text': self.pathology_data.site_name,
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
                'text': self.pathology_data.site_building_address,
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
                'x1': 108,
                'y1': 47,
                'x2': 190,
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
                'x1': 108,
                'y1': 47 + 4 * line,
                'x2': 190,
                'y2': 47 + 4 * (line + 1),
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': f'DDN/DOB: {self.pathology_data.patient_date_of_birth.strftime("%m/%d/%Y")}',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'patient_ramq',
                'type': 'T',
                'x1': 108,
                'y1': 47 + 4 * (line + 1),
                'x2': 190,
                'y2': 47 + 4 * (line + 2),
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': f'NAM/RAMQ: {self.pathology_data.patient_ramq}',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'patient_sites_and_mrns',
                'type': 'T',
                'x1': 108,
                'y1': 47 + 4 * (line + 2),
                'x2': 190,
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

    def _get_report_number_and_date_table(self) -> list[dict[str, Any]]:
        """Build a report number table that is shown inside the main pathology table.

        It contains report number, specimen collected, and specimen report fields.

        Returns:
            dictionary containing data needed to build report number table
        """
        y_position = self.get_y()
        return [
            {
                'name': 'report_number_and_date_box',
                'type': 'B',
                'x1': 28,
                'y1': y_position + 22,
                'x2': 165,
                'y2': y_position + 44,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'box_vertical_separator',
                'type': 'L',
                'x1': 110,
                'y1': y_position + 22,
                'x2': 110,
                'y2': y_position + 44,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'numero_du_rapport',
                'type': 'T',
                'x1': 30,
                'y1': y_position + 23,
                'x2': 64,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': 'Numéro du rapport',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'report_number',
                'type': 'T',
                'x1': 63,
                'y1': y_position + 23,
                'x2': 108,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': '/Report number:',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'report_number_placeholder',
                'type': 'T',
                'x1': 111,
                'y1': y_position + 23,
                'x2': 163,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.pathology_data.test_number,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'numero_du_rapport_separator',
                'type': 'L',
                'x1': 28,
                'y1': y_position + 30,
                'x2': 165,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'echantillon_preleve',
                'type': 'T',
                'x1': 30,
                'y1': y_position + 30,
                'x2': 66,
                'y2': y_position + 37,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': 'Échantillon prélevé',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'specimen_collected',
                'type': 'T',
                'x1': 63,
                'y1': y_position + 30,
                'x2': 120,
                'y2': y_position + 37,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': '/Specimen collected:',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'specimen_collected_placeholder',
                'type': 'T',
                'x1': 111,
                'y1': y_position + 30,
                'x2': 163,
                'y2': y_position + 37,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.pathology_data.test_collected_at.strftime('%Y-%b-%d %H:%M'),
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'specimen_collected_separator',
                'type': 'L',
                'x1': 28,
                'y1': y_position + 37,
                'x2': 165,
                'y2': y_position + 37,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'rapport_sur_lechantillon',
                'type': 'T',
                'x1': 30,
                'y1': y_position + 37,
                'x2': 74,
                'y2': y_position + 44,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': "Rapport sur l'échantillon",
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'specimen_report',
                'type': 'T',
                'x1': 72,
                'y1': y_position + 37,
                'x2': 120,
                'y2': y_position + 44,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': '/Specimen report:',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'specimen_report_placeholder',
                'type': 'T',
                'x1': 111,
                'y1': y_position + 37,
                'x2': 163,
                'y2': y_position + 44,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.pathology_data.test_reported_at.strftime('%Y-%b-%d %H:%M'),
                'priority': 0,
                'multiline': False,
            },
        ]

    def _get_report_prepared_by_table(self) -> list[dict[str, Any]]:
        """Build a "prepared by" table template.

        It is shown at the end of the PDF report after the main content.

        Returns:
            dictionary containing data needed to build a "prepared by" table
        """
        y_position = self.get_y()
        return [
            {
                'name': 'prepared_by_box',
                'type': 'B',
                'x1': 15,
                'y1': y_position,
                'x2': 195,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'prepare_par',
                'type': 'T',
                'x1': 15,
                'y1': y_position + 6,
                'x2': 50,
                'y2': y_position + 10,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': 'Préparé par/',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'prepared_by',
                'type': 'T',
                'x1': 15,
                'y1': y_position + 8,
                'x2': 50,
                'y2': y_position + 15,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 1,
                'underline': 0,
                'align': 'L',
                'text': 'Prepared by:',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'prepared_by_vertical_separator',
                'type': 'L',
                'x1': 85,
                'y1': y_position,
                'x2': 85,
                'y2': y_position + 15,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'prepared_by_placeholder',
                'type': 'T',
                'x1': 86,
                'y1': y_position,
                'x2': 155,
                'y2': y_position + 15,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.pathology_data.prepared_by,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'prepared_by_placeholder_vertical_separator',
                'type': 'L',
                'x1': 155,
                'y1': y_position,
                'x2': 155,
                'y2': y_position + 15,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'prepared_at',
                'type': 'T',
                'x1': 156,
                'y1': y_position,
                'x2': 195,
                'y2': y_position + 15,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.pathology_data.prepared_at.strftime('%d-%b-%Y'),
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'prepared_by_separator',
                'type': 'L',
                'x1': 15,
                'y1': y_position + 15,
                'x2': 195,
                'y2': y_position + 15,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'signe_electroniquement_par',
                'type': 'T',
                'x1': 15,
                'y1': y_position + 15,
                'x2': 60,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': 'Signé électroniquement par/',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'electronically_signed_by',
                'type': 'T',
                'x1': 15,
                'y1': y_position + 17,
                'x2': 60,
                'y2': y_position + 35,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 1,
                'underline': 0,
                'align': 'L',
                'text': 'Electronically signed by:',
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'electronically_signed_by_vertical_separator',
                'type': 'L',
                'x1': 85,
                'y1': y_position + 15,
                'x2': 85,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'electronically_signed_by_placeholder',
                'type': 'T',
                'x1': 86,
                'y1': y_position + 15,
                'x2': 155,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.pathology_data.prepared_by,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'electronically_signed_by_placeholder_vertical_separator',
                'type': 'L',
                'x1': 155,
                'y1': y_position + 15,
                'x2': 155,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
            },
            {
                'name': 'electronically_signed_at_placeholder',
                'type': 'T',
                'x1': 156,
                'y1': y_position + 15,
                'x2': 195,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 10,
                'bold': 0,
                'italic': 0,
                'underline': 0,
                'align': 'L',
                'text': self.pathology_data.prepared_at.strftime('%d-%b-%Y %I:%M %p'),
                'priority': 0,
                'multiline': True,
            },
            {
                'name': 'electronically_signed_by_separator',
                'type': 'L',
                'x1': 15,
                'y1': y_position + 30,
                'x2': 195,
                'y2': y_position + 30,
                'font': PATHOLOGY_REPORT_FONT,
                'size': 0.5,
                'bold': 1,
                'italic': 0,
                'underline': 0,
                'align': 'C',
                'text': None,
                'priority': 0,
                'multiline': False,
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

        The generated report is saved in the directory specified in the PATHOLOGY_REPORTS_PATH environment variable.

        Args:
            pathology_data: pathology data required to generate the PDF report

        Returns:
            path to the generated pathology report
        """
        generated_at = timezone.localtime(timezone.now()).strftime('%Y-%b-%d_%H-%M-%S')
        report_file_name = '{first_name}_{last_name}_{date}_pathology'.format(
            first_name=pathology_data.patient_first_name,
            last_name=pathology_data.patient_last_name,
            date=generated_at,
        )
        report_path = settings.PATHOLOGY_REPORTS_PATH / f'{report_file_name}.pdf'
        pathology_pdf = PathologyPDF(pathology_data)
        pathology_pdf.output(name=str(report_path))

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
