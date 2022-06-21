"""Module providing functionality for a hospital's internal communicatoin (e.g., OIE)."""

import json
from http import HTTPStatus

from django.conf import settings
from django.http import JsonResponse

import requests
from requests.auth import HTTPBasicAuth


class OIECommunicationService:
    """Service that provides functionality for communication with Opal Integration Engine (OIE)."""

    def export_questionnaire_report(
        self,
        report: str,
    ) -> JsonResponse:
        """Send base64 encoded questionnaire report to the OIE.

        Args:
            report (str): questionnaire PDF report in a base64 string format

        Returns:
            JsonResponse: HTTP JSON response
        """
        # TODO: Clarify the requirements for the mrn, site, and destination
        pload = json.dumps({
            'mrn': '999996',
            'site': 'RVH',
            'reportContent': report,
            'docType': 'Opal Completed Questionnaires',
            'documentDate': '2022-06-20 10:17:30',
            'destination': 'Streamline',
        })

        # Try send a request and get a response
        try:
            # TODO: OIE server should support SSL certificates
            response = requests.post(
                settings.OIE_REPORT_POST_URL,
                auth=HTTPBasicAuth(settings.OIE_USER, settings.OIE_PASSWORD),
                json=pload,
                verify=False,  # noqa: S501
            )
        except requests.exceptions.RequestException as req_exp:
            return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message': str(req_exp)})

        # Try to return a JSON object of the response content
        try:
            json_data = response.json()
        except requests.exceptions.JSONDecodeError as decode_err:
            return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message': str(decode_err)})

        return JsonResponse(json_data)
