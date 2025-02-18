# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing custom data structures (a.k.a., named tuples) for the Source System Service."""

from datetime import datetime
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
