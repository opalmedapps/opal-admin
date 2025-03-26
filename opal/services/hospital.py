"""Module providing api functions for the OIE server."""
from django.conf import settings

import requests


def find_patient_by_mrn(mrn: str, site: str):
    """Search patient info by mrn code."""
    url = settings.OIE_HOST
    data = {
        'mrn': mrn,
        'site': site,
        'visitInfo': False,
    }
    response = requests.post(url, data=data)
    return response


def find_patient_by_ramq(ramq: str):
    """Search patient info by ramq code."""
    url = settings.OIE_HOST
    data = {
        'medicareNumber': ramq,
        'visitInfo': False,
    }
    response = requests.post(url, data=data)
    return response
