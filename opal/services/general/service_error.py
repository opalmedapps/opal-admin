# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing functionality for handling errors from external components and generating error messages."""
from typing import Any


class ServiceErrorHandler:
    """Helper that handles external component errors and produces error messages."""

    def generate_error(
        self,
        response_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create error response in a JSON format that contains `data` field with the specific details.

        Args:
            response_data (dict[str, Any]): data that needs to be included into error response message

        Returns:
            dict[str, Any]: error response in JSON format
        """
        return {
            'status': 'error',
            'data': response_data,
        }
