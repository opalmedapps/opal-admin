"""Module providing api functions for the OIE server."""
from http import HTTPStatus
from typing import Dict, cast

from django.conf import settings

import requests


def find_patient_by_mrn(mrn: str, site: str) -> requests.Response:
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
    try:
        response = requests.post(url, data=data)
    except Exception as ex:
        # TODO add the exception to log
        print(ex)
        response = None

    if response is not None:
        if cast(Dict[str, dict], response)['status_code'] != HTTPStatus.OK:
            response = None
    return response


def find_patient_by_ramq(ramq: str) -> requests.Response:
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
    try:
        response = requests.post(url, data=data)
    except Exception as ex:
        # TODO add the exception to log
        print(ex)
        response = None
    if response is not None:
        if cast(Dict[str, dict], response)['status_code'] != HTTPStatus.OK:
            response = None
    return response
