"""Module providing custom data structures (a.k.a., named tuples) for the OIE Service."""
from datetime import datetime
from typing import List, NamedTuple


class OIEReportExportData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for exporting a PDF report to the OIE.

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


class OIEMRNData(NamedTuple):
    """Typed `NamedTuple` that describes MRN fields (a.k.a., MRN data structure) returned from the OIE.

    Attributes:
        mrn (str): one of the patient's MRNs associated with a particular site
        site (str): one of the patient's site codes associated with a particular MRN
        active (bool): MRN is active or not
    """

    site: str
    mrn: str
    active: bool


class OIEPatientData(NamedTuple):
    """Typed `NamedTuple` that describes `Patient` fields (a.k.a., Patient data structure) returned from the OIE.

    Attributes:
        date_of_birth (datetime): the datetime in YYYY-MM-DD HH:II:SS
        first_name (str): patient first name
        last_name (str): patient last name
        sex (str): patient sex
        alias (str): alias name
        ramq (str): health insurance number
        ramq_expiration (datetime): the datetime in YYYY-MM-DD HH:II:SS
        mrns (OIEMRN): list of MRNs
    """

    date_of_birth: datetime
    first_name: str
    last_name: str
    sex: str
    alias: str
    ramq: str
    ramq_expiration: datetime
    mrns: List[OIEMRNData]
