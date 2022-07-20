"""Module providing business logic for the hospital's internal communicatoin (e.g., Opal Integration Engine)."""

import json
from datetime import datetime
from http import HTTPStatus
from typing import NamedTuple

from django.conf import settings
from django.http import JsonResponse

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException


class QuestionnairePDFReport(NamedTuple):
    """Typed `NamedTuple` that describes data fields needed for exporting questionnaire PDF report to the OIE."""

    mrn: str                 # one of the patient's MRNs for the site
    site: str                # one of the patient's site code for the MRN
    base64_content: str      # the base64-encoded PDF
    document_type: str       # the document number (e.g., FMU-... or MU-...)
    document_date: datetime  # the datetime in YYYY-MM-DD HH:II:SS


class OIECommunicationService:
    """Service that provides functionality for communication with Opal Integration Engine (OIE)."""

    def export_questionnaire_report(
        self,
        report_data: QuestionnairePDFReport,
    ) -> JsonResponse:
        """Send base64 encoded questionnaire PDF report to the OIE.

        Args:
            report_data (QuestionnairePDFReport): questionnaire PDF report data needed to call OIE endpoint

        Returns:
            JsonResponse: HTTP JSON response
        """
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
