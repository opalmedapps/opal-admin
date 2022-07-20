"""Module providing business logic for the hospital's internal communicatoin (e.g., Opal Integration Engine)."""

import json
from http import HTTPStatus

from django.conf import settings
from django.http import JsonResponse

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException


class OIECommunicationService:
    """Service that provides functionality for communication with Opal Integration Engine (OIE)."""

    def export_questionnaire_report(
        self,
        mrn: str,
        site: str,
        base64_content: bytes,
        document_type: str,
        document_date,
    ) -> JsonResponse:
        """Send base64 encoded questionnaire PDF report to the OIE.

        Args:
            report (str): questionnaire PDF report in a base64 string format

        Returns:
            JsonResponse: HTTP JSON response
        """
        pload = json.dumps({
            'mrn': '999996',
            'site': 'RVH',
            'reportContent': report,
            'docType': 'Opal Completed Questionnaires',
            'documentDate': '2022-06-20 10:17:30',
            'destination': 'Streamline',
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
