# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing custom data structures (a.k.a., named tuples) for the Source System Service."""
from datetime import date, datetime
from typing import NamedTuple


class SourceSystemReportExportData(NamedTuple):
    """
    Typed `NamedTuple` that describes data fields needed for exporting a PDF report to the Source System.

    Attributes:
        mrn (str): one of the patient's MRNs for the site
        site (str): one of the patient's site code for the MRN
        base64_content (str): the base64-encoded PDF (e.g., questionnaire PDF report)
        document_number (str): the document number (e.g., FMU-... or MU-...)
        document_date (datetime): the datetime in YYYY-MM-DD HH:II:SS
    """

    mrn: str
    site: str
    base64_content: str
    document_number: str
    document_date: datetime


class SourceSystemMRNData(NamedTuple):
    """
    Typed `NamedTuple` that describes MRN fields (a.k.a., MRN data structure) returned from the Source System.

    Attributes:
        mrn (str): one of the patient's MRNs associated with a particular site
        site (str): one of the patient's site codes associated with a particular MRN
        active (bool): MRN is active or not
    """

    site: str
    mrn: str
    active: bool


class SourceSystemPatientData(NamedTuple):
    """
    Typed `NamedTuple` that describes Patient fields (a.k.a., Patient data structure) returned from the SourceSystem.

    Attributes:
        date_of_birth: the date of birth
        first_name: patient first name
        last_name: patient last name
        sex: patient sex
        alias: alias name
        deceased: True if the patient is deceased, False otherwise
        death_date_time: patient death date and time
        ramq: Quebec health insurance number
        ramq_expiration: the expiration date of the health insurance number
        mrns: list of MRNs the patient has
    """

    date_of_birth: date
    first_name: str
    last_name: str
    sex: str
    alias: str
    deceased: bool
    death_date_time: datetime | None
    ramq: str
    ramq_expiration: datetime | None
    mrns: list[SourceSystemMRNData]
