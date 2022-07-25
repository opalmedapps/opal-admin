import json
from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from pytest_mock.plugin import MockerFixture
from requests import Response

from ..patients.factories import HospitalPatient
from ..services.hospital import OIECommunicationService, OIEReportExportData

ENCODING = 'utf-8'
BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_TYPE = 'FMU-8624'

oie_service = OIECommunicationService()

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def _create_report_export_response_data() -> dict[str, str]:
    return {'status': 'success'}


def _mock_requests_post(
    mocker: MockerFixture,
    generated_report_export_response_data: dict[str, str],
) -> MagicMock:
    # mock actual web API call
    mock_post = mocker.patch('requests.post')
    response = Response()
    response.status_code = HTTPStatus.OK

    response._content = json.dumps(generated_report_export_response_data).encode(ENCODING)
    mock_post.return_value = response

    return mock_post


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

def test_export_pdf_report(mocker: MockerFixture) -> None:
    """Ensure successful report export request returns json response with successful HTTP status."""
    hospital_patient = HospitalPatient()

    generated_report_data = _create_report_export_response_data()
    mock_post = _mock_requests_post(mocker, generated_report_data)

    report_data = oie_service.export_pdf_report(
        OIEReportExportData(
            mrn=hospital_patient.mrn,
            site=hospital_patient.site.code,
            base64_content=BASE64_ENCODED_REPORT,
            document_type=DOCUMENT_TYPE,
            document_date=datetime.now(),
        ),
    )

    assert mock_post.return_value.status_code == HTTPStatus.OK
    assert json.loads(report_data.content)['status'] == 'success'
