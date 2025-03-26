"""
This module provides custom fields for the Django REST framework.

These fields are provided for the project and intended to be reused.
"""
from pathlib import Path
from typing import Any, Optional

from django.db.models.fields.files import FieldFile

from rest_framework import serializers

from ..utils.base64_util import Base64Util


class Base64FileField(serializers.Field[FieldFile, FieldFile, Optional[str], Any]):
    """This class is a reuseable field for encoding the file and return the base64 encoded file contents."""

    def to_representation(self, file: FieldFile) -> str | None:
        """Represent a file content in base64 encoded form.

        Args:
            file: The file object

        Returns:
            str: encoded base64 string of the file if the file path is a valid, `None` otherwise
        """
        base64_util = Base64Util()
        return base64_util.encode_to_base64(Path(file.path))
