"""Module providing business logic for the hospital's internal communicatoin (e.g., Opal Integration Engine)."""

import json
import re
from datetime import datetime
from http import HTTPStatus
from typing import NamedTuple

from django.conf import settings
from django.http import JsonResponse

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from opal.utils.base64_util import Base64Util


class OIEReportExportData(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for exporting a PDF report to the OIE.

    Attributes:
        mrn (str): one of the patient's MRNs for the site
        site (str): one of the patient's site code for the MRN
        base64_content (str): the base64-encoded PDF (e.g., questionnaire PDF report)
        document_type (str): the document number (e.g., FMU-... or MU-...)
        document_date (datetime): the datetime in YYYY-MM-DD HH:II:SS
    """

    mrn: str
    site: str
    base64_content: str
    document_type: str
    document_date: datetime


class OIECommunicationService:
    """Service that provides functionality for communication with Opal Integration Engine (OIE)."""

    def export_pdf_report(
        self,
        report_data: OIEReportExportData,
    ) -> JsonResponse:
        """Send base64 encoded PDF report to the OIE.

        Args:
            report_data (OIEReportExportData): PDF report data needed to call OIE endpoint

        Returns:
            JsonResponse: HTTP JSON response
        """
        # return a `JsonResponse` with a BAD_REQUEST if `OIEReportExportData` is not valid
        if not self._is_report_export_data_valid(report_data):
            return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message': 'invalid export data'})

        pload = json.dumps({
            'mrn': report_data.mrn,
            'site': report_data.site,
            'reportContent': report_data.base64_content,
            'docType': report_data.document_type,
            'documentDate': report_data.document_date,
        })

        # Try to send a request and get a response
        try:
            # TODO: OIE server should support SSL certificates. This will allow to use `verify=True` that fixes S501
            response = requests.post(
                '{0}{1}'.format(settings.OIE_HOST, 'reports/post'),
                auth=HTTPBasicAuth(settings.OIE_USER, settings.OIE_PASSWORD),
                json=pload,
                timeout=5,
                verify=False,  # noqa: S501
            )
        except RequestException as req_exp:
            return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message': str(req_exp)})

        # Try to return a JSON object of the response content
        try:
            json_data = response.json()
        except requests.exceptions.JSONDecodeError as decode_err:
            return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message': str(decode_err)})

        return JsonResponse(json_data)

    def _is_report_export_data_valid(self, report_data: OIEReportExportData) -> bool:
        """Check if OIE report export data is valid.

        Args:
            report_data (OIEReportExportData): OIE report export data needed to call OIE endpoint

        Returns:
            bool: boolean value showing if OIE report export data is valid
        """
        # check if mrn exists
        # if LegacyPatientHospitalIdentifier.objects.filter(MRN=report_data.mrn).exists()

        # check if site exists
        # if LegacyPatientHospitalIdentifier.objects.filter(
        # Hospital_Identifier_Type_Code=report_data.site
        # ).exists()

        return (  # check if report content is base64
            Base64Util().base64_util.is_base64(report_data.base64_content)
            # check if document type format is valid?
            and re.compile('(^FU-[a-zA-Z]+$)|(^FMU-[a-zA-Z]+$)')
            # check document date?
        )
