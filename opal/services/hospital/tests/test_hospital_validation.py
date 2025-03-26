from datetime import datetime

from opal.services.hospital.hospital_data import OIEReportExportData
from opal.services.hospital.hospital_validation import OIEValidator

BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
MRN = '9999996'
SITE_CODE = 'MUHC'

oie_validator = OIEValidator()


# is_report_export_request_valid

def test_is_report_export_request_valid_success() -> None:
    """Ensure `OIEReportExportData` successfully validates."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_validator.is_report_export_request_valid(report_data)


def test_is_report_export_request_invalid_mrn() -> None:
    """Ensure `OIEReportExportData` with invalid MRN are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn='',
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_site() -> None:
    """Ensure `OIEReportExportData` with invalid site are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site='',
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_content() -> None:
    """Ensure `OIEReportExportData` with invalid base64 content are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content='INVALID CONTENT',
        document_number=DOCUMENT_NUMBER,
        document_date=datetime.now(),
    )

    assert oie_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_doctype() -> None:
    """Ensure `OIEReportExportData` with invalid document type are handled and does not result in an error."""
    report_data = OIEReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number='FU-INVALID DOCUMENT TYPE',
        document_date=datetime.now(),
    )

    assert oie_validator.is_report_export_request_valid(report_data) is False


# is_report_export_response_valid

def test_is_report_export_response_valid_success() -> None:
    """Ensure report export response data successfully validates."""
    assert oie_validator.is_report_export_response_valid({'status': 'success'}) is True
    assert oie_validator.is_report_export_response_valid({'status': 'error'}) is True


def test_is_report_export_response_invalid() -> None:
    """Ensure that report export invalid response data are handled and do not result in an error."""
    assert oie_validator.is_report_export_response_valid({'invalid': 'invalid'}) is False
    assert oie_validator.is_report_export_response_valid({'invalid': 'success'}) is False
    assert oie_validator.is_report_export_response_valid({'invalid': 'error'}) is False
    assert oie_validator.is_report_export_response_valid({}) is False


def test_is_report_export_response_invalid_type() -> None:
    """Ensure that report export invalid response data type is handled and does not result in an error."""
    assert oie_validator.is_report_export_response_valid({'status': {}}) is False
    assert oie_validator.is_report_export_response_valid(None) is False
    assert oie_validator.is_report_export_response_valid('test string') is False
    assert oie_validator.is_report_export_response_valid(123) is False
    assert oie_validator.is_report_export_response_valid({'status': {'success'}}) is False
