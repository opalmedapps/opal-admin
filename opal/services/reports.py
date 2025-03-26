"""Module providing business logic for generating PDF reports using legacy PHP endpoints."""

import base64
import imghdr
import json
from pathlib import Path

from django.conf import settings

import requests
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import status

from opal.legacy.models import LegacyPatient


class ReportService():
    """Service that provides functionality for generating questionnaire pdf reports."""

    content_type = 'application/json'

    def generate_questionnaire_report(
        self,
        patient_id: int,
        logo_path: Path,
        language: str,
    ) -> str:
        """Create PDF report in encoded base64 string format.

        Args:
            patient_id (int): the ID of an Opal patient
            logo_path (Path): file path of the logo image
            language (str): report's language (English or French)

        Returns:
            str: encoded base64 string of the generated PDF report
        """
        # return an empty string if patient_id (PatientSerNum) does not exist
        if not LegacyPatient.objects.filter(patientsernum=patient_id).exists():
            return ''

        # return an empty string if logo_path does not exist
        if not logo_path.exists():
            return ''

        # return an empty string if language does not exist
        languages = dict(settings.LANGUAGES)
        if language not in languages:
            return ''

        base64_report = self._request_base64_report(patient_id, logo_path, language)

        return base64_report if self._is_base64(base64_report) is True else ''

    def _request_base64_report(
        self,
        patient_id: int,
        logo_path: Path,
        language: str,
    ) -> str:
        """Generate a PDF report by making an HTTP call to the legacy PHP endpoint.

        Args:
            patient_id (int): the ID of an Opal patient
            logo_path (Path): file path of the logo image
            language (str): report's language (English or French)

        Returns:
            str: encoded base64 string of the generated PDF report
        """
        pload = json.dumps({
            'patient_id': patient_id,
            'logo_base64': self._encode_image_to_base64(logo_path),
            'language': language,
        })

        headers = {'Content-Type': self.content_type}

        try:
            response = requests.post(
                url=settings.LEGACY_QUESTIONNAIRES_REPORT_URL,
                headers=headers,
                data=pload,
            )
        except RequestException:
            return ''

        # Return an empty string if response status code is not success (e.g, different than 2**)
        if status.is_success(response.status_code) is False:
            return ''

        # Return an empty string if cannot read encoded pdf report
        try:
            base64_report = response.json()['data']['base64EncodedReport']
        except (KeyError, JSONDecodeError):
            return ''

        # Check if ['data']['base64EncodedReport'] is a string and return its value. If not a string, return empty one.
        return base64_report if isinstance(base64_report, str) else ''

    def _encode_image_to_base64(self, logo_path: Path) -> str:
        """Create base64 string of a given image.

        Args:
            logo_path (Path): file path of the logo image

        Returns:
            str: encoded base64 string of the logo image
        """
        try:
            # Return an empty string if a given file is not an image
            if imghdr.what(logo_path) is None:
                return ''
        except IOError:
            return ''

        try:
            with logo_path.open(mode='rb') as image_file:
                data = base64.b64encode(image_file.read())
        except IOError:
            return ''

        return data.decode('utf-8')

    def _is_base64(self, string: str) -> bool:
        """Check if a given string is base64 encoded.

        Args:
            string (str): encoded base64 string

        Returns:
            bool: if a given string is base64
        """
        # base64 string cannot be empty
        if not string:
            return False

        try:
            return base64.b64encode(base64.b64decode(string)) == bytes(string, 'ascii')
        except ValueError:
            return False
