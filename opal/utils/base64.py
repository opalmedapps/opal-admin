"""Module providing an utility for base64 encoding operations."""

import base64
import imghdr
from pathlib import Path


class Base64Util:
    """Util that provides functionality for handling base64 encoding strings."""

    def encode_image_to_base64(self, logo_path: Path) -> str:
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
        except OSError:
            return ''

        try:
            with logo_path.open(mode='rb') as image_file:
                data = base64.b64encode(image_file.read())
        except OSError:
            return ''

        return data.decode('utf-8')

    def is_base64(self, string: str) -> bool:
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
            return (
                base64.b64encode(base64.b64decode(string, validate=True)) == bytes(string, 'ascii')
            )
        except (ValueError, TypeError):
            return False
