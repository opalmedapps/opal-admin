"""Module providing api functions for the OIE server."""
from http import HTTPStatus
from typing import Dict

from django.conf import settings

import requests


class OIECommunicationService:
    """Service that provides functionality for communication with Opal Integration Engine (OIE)."""

    def find_patient_by_mrn(self, mrn: str, site: str) -> Dict:
        """Search patient info by mrn code.

        Args:
            mrn: mrn code
            site: site name

        Returns:
            return the reponse of the OIE
        """
        url = settings.OIE_HOST
        data = {
            'mrn': mrn,
            'site': site,
            'visitInfo': False,
        }
        response = requests.post(url, data=data)
        if response.status_code == HTTPStatus.OK:
            result = {data: response.json()}
        else:
            result = {data: None}
        return result

    def find_patient_by_ramq(self, ramq: str) -> requests.Response:
        """Search patient info by ramq code.

        Args:
            ramq: ramq code

        Returns:
            return the reponse of the OIE
        """
        url = settings.OIE_HOST
        data = {
            'medicareNumber': ramq,
            'visitInfo': False,
        }
        response = requests.post(url, data=data)
        if response.status_code == HTTPStatus.OK:
            result = {data: response.json()}
        else:
            result = {data: None}
        return result
