"""Module providing an utility for base64 encoding operations."""

import base64
from pathlib import Path
from typing import Optional


class Base64Util:
    """Util that provides functionality for handling base64 encoding strings."""

    def encode_to_base64(self, path: Path) -> Optional[str]:
        """Create base64 string of a given image.

        Args:
            path (Path): file path of the logo image

        Returns:
            str: encoded base64 string of the logo image if the `logo_path` is a valid image file, `None` otherwise
        """
        try:
            # Return a `None` if a given file is not an image
            with path.open(mode='rb') as image_file:
                data = base64.b64encode(image_file.read())
        except OSError:
            return None

        return data.decode('utf-8')

    def is_base64(self, string: Optional[str]) -> bool:
        """Check if a given string is base64 encoded.

        Args:
            string (str): encoded base64 string

        Returns:
            bool: if a given string is base64
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
