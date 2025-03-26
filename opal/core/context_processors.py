"""This module provides custom context processors for this project."""
from typing import Dict

from django.conf import settings
from django.http import HttpRequest


def opal_global_settings(request: HttpRequest) -> Dict:
    """
    Provide custom context processor that returns a dictionary with the `OpalAdmin` global values.

    Args:
        request: `HttpRequest` object

    Returns:
        dictionary that contains `OpalAdmin` global values (e.g., OpalAdmin URL, media URL, etc.).
    """
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        'OPAL_ADMIN_URL': settings.OPAL_ADMIN_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
