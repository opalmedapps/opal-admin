"""Module providing business logic for the hospital's internal communicatoin (e.g., Opal Integration Engine)."""


from datetime import datetime
from typing import Any, NamedTuple

from .hospital_communication import OIEHTTPCommunicationManager
from .hospital_error import OIEErrorHandler
from .hospital_validation import OIEValidator


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


class OIEService:
    """Service that provides an interface (a.k.a., Facade) for interaction with the Opal Integration Engine (OIE).

    All the provided functions contain the following business logic:
        * validate the input data (a.k.a., parameters)
        * send an HTTP request to the OIE
        * validate the response data received from the OIE
        * return response data or an error in JSON format
    """

    def __init__(self) -> None:
        """Initialize OIE helper services."""
        self.communication_manager = OIEHTTPCommunicationManager()
        self.error_handler = OIEErrorHandler()
        self.validator = OIEValidator()

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
        # Return a JSON format error if `OIEReportExportData` is not valid
        if not self.validator.is_report_export_request_valid(report_data):
            return self.error_handler.generate_error(
                {'message': 'Provided request data are invalid.'},
            )

        # TODO: Change docType to docNumber once the OIE's endpoint is updated
        payload = {
            'mrn': report_data.mrn,
            'site': report_data.site,
            'reportContent': report_data.base64_content,
            'docType': report_data.document_number,
            'documentDate': report_data.document_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

        response_data = self.communication_manager.submit(
            endpoint='/reports/post',
            payload=payload,
        )

        if self.validator.is_report_export_response_valid(response_data):
            return response_data

        return self.error_handler.generate_error(
            {
                'message': 'OIE response format is not valid.',
                'responseData': response_data,
            },
        )
