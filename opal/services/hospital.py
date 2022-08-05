"""Module providing business logic for the hospital's internal communicatoin (e.g., Opal Integration Engine)."""


from datetime import datetime
from typing import Any, NamedTuple

import hospital_error
import hospital_validation

from .hospital_communication import OIEHTTPCommunicationManager


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


class OIECommunicationService:
    """Service that provides functionality for communication with Opal Integration Engine (OIE)."""

    def export_pdf_report(
        self,
        report_data: OIEReportExportData,
    ) -> Any:
        """Send base64 encoded PDF report to the OIE.

        Args:
            report_data (OIEReportExportData): PDF report data needed to call OIE endpoint

        Returns:
            Any: JSON object response
        """
        # Return a `JsonResponse` with a BAD_REQUEST if `OIEReportExportData` is not valid
        if not hospital_validation.is_report_export_data_valid(report_data):
            return hospital_error.generate_json_error({'message': 'Provided request data are invalid.'})

        # TODO: Change docType to docNumber once the OIE's endpoint is updated
        payload = {
            'mrn': report_data.mrn,
            'site': report_data.site,
            'reportContent': report_data.base64_content,
            'docType': report_data.document_number,
            'documentDate': report_data.document_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

        communication_manager = OIEHTTPCommunicationManager()
        response_data = communication_manager.submit(
            endpoint='/reports/post',
            payload=payload,
        )

        if hospital_validation.is_report_export_response_valid(response_data):
            return response_data

        return hospital_error.generate_json_error(
            {
                'message': 'OIE response format is not valid.',
                'responseData': response_data,
            },
        )
