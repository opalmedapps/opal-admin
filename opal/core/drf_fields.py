# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
This module provides custom fields for the Django REST framework.

These fields are provided for the project and intended to be reused.
"""

from pathlib import Path
from typing import Any

from django.db.models.fields.files import FieldFile

from rest_framework import serializers

from ..utils import base64_utils


class Base64FileField(serializers.Field[FieldFile, FieldFile, str | None, Any]):
    """This class is a reusable field for encoding the file and return the base64 encoded file contents."""

    def to_representation(self, file: FieldFile) -> str | None:
        """
        Represent a file content in base64 encoded form.

        Args:
            file: The file object

        Returns:
            str: encoded base64 string of the file if the file path is a valid, `None` otherwise
        """
        return base64_utils.file_to_base64(Path(file.path))
