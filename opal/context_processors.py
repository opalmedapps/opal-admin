"""This module provides custom context processors for this project."""
from typing import Dict

from django.conf import settings
from django.http import HttpRequest


def opal_admin(request: HttpRequest) -> Dict:
    """
    Provide custom context processor that returns a dictionary with the `OpalAdmin` URL.

    Args:
        request: `HttpRequest` object

    Returns:
        dictionary that contains `OpalAdmin` URL under the key `OPAL_ADMIN_URL`.
    """
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'OPAL_ADMIN_URL': settings.OPAL_ADMIN_URL}
