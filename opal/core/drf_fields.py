"""
This module provides custom fieldss for the Django REST framework.

These fields are provided for the project and intended to be reused.
"""
from pathlib import Path
from typing import Optional

from rest_framework import serializers

from ..utils.base64 import Base64Util


class Base64PDFFileField(serializers.Field):
    """This class is a reuseable field for encoding the to read the file and return the base64 encoded file contents."""

    def to_representation(self, path: str) -> Optional[str]:
        """Represent a pdf file content in base64 encoded form.

        Args:
            path (str): The file path of the pdf file

        Returns:
            str: encoded base64 string of the pdf file if the `path` is a valid pdf file, `None` otherwise
        """
        base64_util = Base64Util()
        return base64_util.encode_pdf_to_base64(Path(path))
