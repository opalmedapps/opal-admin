"""Module providing utility functions for base64 encoding operations."""

import base64
from pathlib import Path


def file_to_base64(path: Path) -> str | None:
    """Create a base64 string of a given file.

    Args:
        path: file path

    Returns:
        str: encoded base64 string of the input file if the `path` is a valid file path, `None` otherwise
    """
    try:
        with path.open(mode='rb') as file:
            data = base64.b64encode(file.read())
    except OSError:
        return None

    return data.decode('utf-8')


def is_base64(string: str | None) -> bool:
    """Check if a given string is base64 encoded.

    Args:
        string: encoded base64 string

    Returns:
        True, if given string is base64, False otherwise
    """
    # base64 string cannot be empty or None
    if not string:
        return False

    try:
        return (
            base64.b64encode(base64.b64decode(string, validate=True)) == bytes(string, 'ascii')
        )
    except (ValueError, TypeError):
        return False
