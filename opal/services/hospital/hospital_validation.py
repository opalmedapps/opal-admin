# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing validation rules for the data being sent/received to/from the source system."""

import re
from typing import Any

from opal.utils import base64_utils

from .hospital_data import SourceSystemReportExportData

# TODO: translate error messages add _(message) that will be shown to the user.


class SourceSystemValidator:
    """Source system helper service that validates source system request and response data."""

    def is_report_export_request_valid(
        self,
        report_data: SourceSystemReportExportData,
    ) -> bool:
        """
        Check if the source system report export data is valid.

        Args:
            report_data (SourceSystemReportExportData): Source system report export data needed to
                                                        call source system endpoint

        Returns:
            bool: boolean value showing if source system report export data is valid
        """
        # TODO: Add more validation/checks for the MRN and Site fields once the requirements are clarified
        # TODO: Confirm the regex pattern for the document number
        reg_exp = re.compile(r'(^FU-[a-zA-Z0-9]+$)|(^FMU-[a-zA-Z0-9]+$)|(^MU-[a-zA-Z0-9]+$)')
        return (  # check if MRN is not empty
            bool(report_data.mrn.strip())
            # check if site is not empty
            and bool(report_data.site.strip())
            # check if report content is base64
            and base64_utils.is_base64(report_data.base64_content)
            # check if document type format is valid
            and bool(reg_exp.match(report_data.document_number))
        )

    def is_report_export_response_valid(
        self,
        response_data: Any,
    ) -> bool:
        """
        Check if the source system report export response data is valid.

        Args:
            response_data (Any): Source system report export response data received from the source system

        Returns:
            bool: boolean value showing if source system report export data is valid
        """
        try:
            status = response_data['status']
        except (TypeError, KeyError):
            return False

        # TODO: confirm validation rules (e.g., status in {'success', 'error'})
        return isinstance(status, str)
