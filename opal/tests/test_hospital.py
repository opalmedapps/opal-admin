from datetime import datetime

import pytest

from ..patients.factories import HospitalPatient
from ..services.hospital import OIECommunicationService, OIEReportExportData

BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_TYPE = 'FMU-8624'

oie_service = OIECommunicationService()

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


# _is_report_export_data_valid

def test_is_report_export_data_valid_success() -> None:
    """Ensure `OIEReportExportData` successfully validates."""
    hospital_patient = HospitalPatient()

    report_data = OIEReportExportData(
        mrn=hospital_patient.mrn,
        site=hospital_patient.site.code,
        base64_content=BASE64_ENCODED_REPORT,
        document_type=DOCUMENT_TYPE,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data)


def test_is_report_export_data_invalid_mrn() -> None:
    """Ensure `OIEReportExportData` with invalid MRN are handled and does not result in an error."""
    hospital_patient = HospitalPatient()

    report_data = OIEReportExportData(
        mrn='INVALID MRN',
        site=hospital_patient.site.code,
        base64_content=BASE64_ENCODED_REPORT,
        document_type=DOCUMENT_TYPE,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


def test_is_report_export_data_invalid_site() -> None:
    """Ensure `OIEReportExportData` with invalid site are handled and does not result in an error."""
    hospital_patient = HospitalPatient()

    report_data = OIEReportExportData(
        mrn=hospital_patient.mrn,
        site='INVALID SITE',
        base64_content=BASE64_ENCODED_REPORT,
        document_type=DOCUMENT_TYPE,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


def test_is_report_export_data_invalid_content() -> None:
    """Ensure `OIEReportExportData` with invalid base64 content are handled and does not result in an error."""
    hospital_patient = HospitalPatient()

    report_data = OIEReportExportData(
        mrn=hospital_patient.mrn,
        site=hospital_patient.site.code,
        base64_content='INVALID CONTENT',
        document_type=DOCUMENT_TYPE,
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


def test_is_report_export_data_invalid_doc_type() -> None:
    """Ensure `OIEReportExportData` with invalid document type are handled and does not result in an error."""
    hospital_patient = HospitalPatient()

    report_data = OIEReportExportData(
        mrn=hospital_patient.mrn,
        site=hospital_patient.site.code,
        base64_content=BASE64_ENCODED_REPORT,
        document_type='FU-INVALID DOCUMENT TYPE',
        document_date=datetime.now(),
    )

    assert oie_service._is_report_export_data_valid(report_data) is False


# export_pdf_report
