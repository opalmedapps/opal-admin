"""Module providing business logic for the hospital's internal communication (e.g., Opal Integration Engine)."""

from typing import Any

from .hospital_communication import OIEHTTPCommunicationManager
from .hospital_data import OIEReportExportData
from .hospital_error import OIEErrorHandler
from .hospital_validation import OIEValidator


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
            endpoint=':6682/reports/post',
            payload=payload,
        )

        if self.validator.is_report_export_response_valid(response_data):
            # TODO: confirm return format
            return response_data

        return self.error_handler.generate_error(
            {
                'message': 'OIE response format is not valid.',
                'responseData': response_data,
            },
        )
