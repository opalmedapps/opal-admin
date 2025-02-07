# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utility classes used by management commands or in the testing of management commands."""
import json
from http import HTTPStatus
from io import StringIO
from typing import Any

from django.core.management import call_command

import requests
from pytest_mock import MockerFixture, MockType


class CommandTestMixin:
    """Mixin to facilitate testing of management commands."""

    def _call_command(self, command_name: str, *args: Any, **kwargs: Any) -> tuple[str, str]:
        """
        Call a management command and return the command's standard and error output.

        Args:
            command_name: specify the command name to run
            args: non-keyword input parameter
            kwargs: keywords input parameter

        Returns:
            tuple of stdout and stderr output
        """
        out = StringIO()
        err = StringIO()
        call_command(
            command_name,
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()


class RequestMockerTest:
    """Class that provides methods to mock HTTP requests."""

    @classmethod
    def mock_requests_post(
        cls,
        mocker: MockerFixture,
        response_data: dict[str, Any],
    ) -> MockType:
        """
        Mock an HTTP POST call to a web service.

        Args:
            mocker: object that provides the same interface to functions in the mock module
            response_data: generated mock response data

        Returns:
            object that mocks HTTP post request to the web service
        """
        mock_post = mocker.patch('requests.post')
        response = requests.Response()
        response.status_code = HTTPStatus.OK

        response._content = json.dumps(response_data).encode()  # noqa: SLF001
        mock_post.return_value = response

        return mock_post

    @classmethod
    def mock_requests_get(
        cls,
        mocker: MockerFixture,
        generated_response_data: dict[str, str],
    ) -> MockType:
        """
        Mock an HTTP GET call to a web service.

        Args:
            mocker: object that provides the same interface to functions in the mock module
            generated_response_data: generated mock response data

        Returns:
            object that mocks HTTP get request to the web service
        """
        mock_get = mocker.patch('requests.get')
        response = requests.Response()
        response.status_code = HTTPStatus.OK

        response._content = json.dumps(generated_response_data).encode()  # noqa: SLF001
        mock_get.return_value = response

        return mock_get
