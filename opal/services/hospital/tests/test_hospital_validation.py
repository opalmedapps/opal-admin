# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from django.utils import timezone

from opal.services.hospital.hospital_data import SourceSystemReportExportData
from opal.services.hospital.hospital_validation import SourceSystemValidator

BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
MRN = '9999996'
SITE_CODE = 'MUHC'

source_system_validator = SourceSystemValidator()


# is_report_export_request_valid


def test_is_report_export_request_valid_success() -> None:
    """Ensure `SourceSystemReportExportData` successfully validates."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data)


def test_is_report_export_request_invalid_mrn() -> None:
    """Ensure `SourceSystemReportExportData` with invalid MRN are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn='',
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_site() -> None:
    """Ensure `SourceSystemReportExportData` with invalid site are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site='',
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_content() -> None:
    """Ensure `SourceSystemReportExportData` with invalid base64 content are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content='INVALID CONTENT',
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_doctype() -> None:
    """Ensure `SourceSystemReportExportData` with invalid document type are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number='FU-INVALID DOCUMENT TYPE',
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


# is_report_export_response_valid


def test_is_report_export_response_valid_success() -> None:
    """Ensure report export response data successfully validates."""
    assert source_system_validator.is_report_export_response_valid({'status': 'success'}) is True
    assert source_system_validator.is_report_export_response_valid({'status': 'error'}) is True


def test_is_report_export_response_invalid() -> None:
    """Ensure that report export invalid response data are handled and do not result in an error."""
    assert source_system_validator.is_report_export_response_valid({'invalid': 'invalid'}) is False
    assert source_system_validator.is_report_export_response_valid({'invalid': 'success'}) is False
    assert source_system_validator.is_report_export_response_valid({'invalid': 'error'}) is False
    assert source_system_validator.is_report_export_response_valid({}) is False


def test_is_report_export_response_invalid_type() -> None:
    """Ensure that report export invalid response data type is handled and does not result in an error."""
    assert source_system_validator.is_report_export_response_valid({'status': {}}) is False
    assert source_system_validator.is_report_export_response_valid(None) is False
    assert source_system_validator.is_report_export_response_valid('test string') is False
    assert source_system_validator.is_report_export_response_valid(123) is False
    assert source_system_validator.is_report_export_response_valid({'status': {'success'}}) is False
