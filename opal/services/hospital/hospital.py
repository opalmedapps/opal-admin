# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing business logic for the hospital's internal communication (e.g., Opal Integration Engine)."""

from typing import Any

from ..general.service_error import ServiceErrorHandler
from .hospital_communication import SourceSystemHTTPCommunicationManager
from .hospital_data import SourceSystemReportExportData
from .hospital_validation import SourceSystemValidator


class SourceSystemService:
    """
    Service that provides an interface (a.k.a., Facade) for interaction with the Integration Engine.

    All the provided functions contain the following business logic:
        * validate the input data (a.k.a., parameters)
        * send an HTTP request to the Source system
        * validate the response data received from the Source system
        * return response data or an error in JSON format
    """

    def __init__(self) -> None:
        """Initialize source system helper services."""
        self.communication_manager = SourceSystemHTTPCommunicationManager()
        self.error_handler = ServiceErrorHandler()
        self.validator = SourceSystemValidator()

    def export_pdf_report(
        self,
        report_data: SourceSystemReportExportData,
    ) -> Any:
        """
        Send base64 encoded PDF report to the source system.

        Args:
            report_data (SourceSystemReportExportData): PDF report data needed to call Source System endpoint

        Returns:
            Any: JSON object response
        """
        # Return a JSON format error if `SourceSystemReportExportData` is not valid
        if not self.validator.is_report_export_request_valid(report_data):
            return self.error_handler.generate_error(
                {'message': 'Provided request data are invalid.'},
            )

        # TODO: Change docType to docNumber once the source system endpoint is updated
        payload = {
            'mrn': report_data.mrn,
            'site': report_data.site,
            'reportContent': report_data.base64_content,
            'docType': report_data.document_number,
            'documentDate': report_data.document_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

        response_data = self.communication_manager.submit(
            endpoint='/report/post',
            payload=payload,
        )

        if self.validator.is_report_export_response_valid(response_data):
            # TODO: confirm return format
            return response_data

        return self.error_handler.generate_error(
            {
                'message': 'Source system response format is not valid.',
                'responseData': response_data,
            },
        )
