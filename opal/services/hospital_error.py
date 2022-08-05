"""Module providing functionality for handling Opal Integration Engine (OIE) errors and generating error messages."""
from typing import Any


def generate_json_error(
    response_data: dict[str, Any],
) -> dict[str, Any]:
    """Create error response in a JSON format that contains `data` field with the specific details.

    Args:
        response_data (dict[str, Any]): data that needs to be included into error response

    Returns:
        dict[str, Any]: error response in JSON format
    """
    return {
        'status': 'error',
        'data': response_data,
    }
