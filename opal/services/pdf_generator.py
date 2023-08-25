"""Module providing business logic for generating PDFs using fpdf2 library."""

import logging

from fpdf import FPDF, FlexTemplate

LOGGER = logging.getLogger()


class PDFGenerator(FPDF):
    """Service that provides functionality for generating PDF documents."""
    def header(self):
        # Rendering logo:
        # self.image("../docs/fpdf2-logo.png", 10, 8, 33)
        # Setting font: helvetica bold 15
        self.set_font('helvetica', 'B', 15)
        # Moving cursor to the right:
        self.cell(80)
        # Printing title:
        self.cell(30, 10, 'Title', border=1, align='C')
        # Performing a line break:
        self.ln(20)

    def footer(self):
        # Position cursor at 1.5 cm from bottom:
        self.set_y(-15)
        # Setting font: helvetica italic 8
        self.set_font('arial', 'B', 12)
        # Printing page number:
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='R')
        # Line break; 50mm from each edge
        # self.line(50, 45, 210-50, 45)
