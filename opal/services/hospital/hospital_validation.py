"""Module providing validation rules for the data being sent/received to/from the OIE."""
import re
from typing import Any

from opal.utils.base64 import Base64Util

from .hospital_data import OIEReportExportData


class OIEValidator:
    """OIE helper service that validates OIE request and response data."""

    def is_report_export_request_valid(
        self,
        report_data: OIEReportExportData,
    ) -> bool:
        """Check if the OIE report export data is valid.

        Args:
            report_data (OIEReportExportData): OIE report export data needed to call OIE endpoint

        Returns:
            bool: boolean value showing if OIE report export data is valid
        """
        # TODO: Add more validation/checks for the MRN and Site fields once the requirements are clarified
        # TODO: Confirm the regex pattern for the document number
        reg_exp = re.compile('(^FU-[a-zA-Z0-9]+$)|(^FMU-[a-zA-Z0-9]+$)')
        return (  # check if MRN is not empty
            bool(report_data.mrn.strip())
            # check if site is not empty
            and bool(report_data.site.strip())
            # check if report content is base64
            and Base64Util().is_base64(report_data.base64_content)
            # check if document type format is valid
            and bool(reg_exp.match(report_data.document_number))
        )

    def is_report_export_response_valid(
        self,
        response_data: Any,
    ) -> bool:
        """Check if the OIE report export response data is valid.

        Args:
            response_data (Any): OIE report export response data received from the OIE

        Returns:
            bool: boolean value showing if OIE report export data is valid
        """
        try:
            status = response_data['status']
        except (TypeError, KeyError):
            return False

        # TODO: confirm validation rules (e.g., status in {'success', 'error'})
        return isinstance(status, str)
