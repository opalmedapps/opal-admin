# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Shared functionality for report generation functionality."""

from datetime import date
from pathlib import Path
from typing import Literal, NamedTuple

from fpdf import Align
from typing_extensions import TypedDict


class FPDFCellDictType(TypedDict):
    """The required arguments to pass to FPDF's cell() function."""

    w: float | None
    h: float | None
    text: str
    border: bool | str | Literal[0, 1]
    align: str | Align
    link: str | int
    markdown: bool


class FPDFMultiCellDictType(TypedDict):
    """The required arguments to pass to FPDF's multi_cell() function."""

    w: float
    h: float | None
    text: str
    align: str | Align


class FPDFFontDictType(TypedDict):
    """The required arguments to pass to FPDF's set_font() function."""

    family: str | None
    style: Literal['', 'B', 'I', 'U', 'BU', 'UB', 'BI', 'IB', 'IU', 'UI', 'BIU', 'BUI', 'IBU', 'IUB', 'UBI', 'UIB']
    size: int


class FPDFRectDictType(TypedDict):
    """The required arguments to pass to FPDF's rect() function."""

    x: float
    y: float
    w: float
    h: float
    style: str | None


class InstitutionData(NamedTuple):
    """
    Information about an institution from which a report was received.

    Attributes:
        institution_logo_path: file path of the instituion's logo image
        document_number: the unique number assigned in the hospital system for this type of document
        source_system: the name of the system that generated the document
    """

    institution_logo_path: Path
    document_number: str
    source_system: str


class SiteData(NamedTuple):
    """
    Information about a hospital site from which a report was received.

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
    """
    Typed `NamedTuple` that describes data fields for storing patient's personal information.

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
