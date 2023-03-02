"""This module provides custom context processors for this project."""
from typing import Any

from django.apps import apps
from django.conf import settings
from django.http import HttpRequest


def opal_global_settings(request: HttpRequest) -> dict[str, Any]:
    """
    Provide custom context processor that returns a dictionary with the `OpalAdmin` global values.

    Args:
        request: `HttpRequest` object

    Returns:
        dictionary that contains `OpalAdmin` global values (e.g., OpalAdmin URL).
    """
    return {
        'OPAL_ADMIN_URL': settings.OPAL_ADMIN_URL,
    }


def current_app(request: HttpRequest) -> dict[str, Any]:
    app_name = request.resolver_match.app_name.replace('-', '_')  # type: ignore[union-attr]

    return {
        'app_verbose_name': apps.get_app_config(app_name).verbose_name,
    }
