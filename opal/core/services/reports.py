"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import base64
import json

from django.conf import settings

import requests
from rest_framework import status

from opal.report_settings.models import ReportTemplate


class QuestionnaireReportService():
    """Service that provides functionality for generating questionnaire pdf reports."""

    content_type = 'application/json'

    def generate(self, patient_id: int, language: str) -> str:
        """Create PDF report in encoded base64 string format by using legacy PHP endpoints.

        Args:
            patient_id (int): the ID of an Opal patient
            language (str): report's language (English or French)

        Returns:
            str: encoded base64 string
        """
        logo_url = ReportTemplate.objects.filter(name__iexact='Questionnaires').first().logo.url  # type: ignore

        pload = json.dumps({
            'patient_id': patient_id,
            'logo_url': logo_url,
            'language': language,
        })

        headers = {'Content-Type': self.content_type}
        response = requests.post(settings.LEGACY_QUESTIONNAIRES_REPORT_URL, headers=headers, data=pload)
        base64_report: str = ''

        # Return an empty string if response status code is not success (e.g, different than 2**)
        if status.is_success(response.status_code) is False:
            return ''

        # Return an empty string if cannot read encoded pdf report
        try:
            base64_report = response.json()['data']['base64EncodedReport']
        except KeyError:
            return ''

        return base64_report if self._is_base64(base64_report) is True else ''

    def _is_base64(self, string: str) -> bool:
        """Check if a given string is base64 encoded.

        Args:
            string (str): encoded base64 string

        Returns:
            bool: if a given string is base64
        """
        try:
            return base64.b64encode(base64.b64decode(string)) == bytes(string, 'ascii')
        except Exception:
            return False
