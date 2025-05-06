# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing business logic for communication with an external component."""

import json
import logging
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from .service_error import ServiceErrorHandler

# add this in any module that need to log
logger = logging.getLogger(__name__)

# hard-coded source system timeout
SOURCE_SYSTEM_TIMEOUT = 30


class ServiceHTTPCommunicationManager:
    """
    Manager that provides functionality for communication with an external component.

    The manager is responsible only for the HTTP communication and handling any communication-related errors.

    The manager is not responsible for the data content being transferred.
    """

    base_url: str
    display_name: str
    user: str
    password: str
    dump_json_payload: bool

    def __init__(
        self,
        base_url: str,
        display_name: str,
        user: str,
        password: str,
        dump_json_payload: bool,
    ) -> None:
        """
        Initialize service-specific values and handlers.

        Args:
            base_url: The base URL of the service with which to communicate.
            display_name: A short string used to represent the service in logger messages.
            user: The username with which to authenticate with the service.
            password: The password with which to authenticate with the service.
            dump_json_payload: If true, json.dumps() is applied to the JSON payload in post requests.
        """
        # Service-specific values
        self.base_url = base_url
        self.display_name = display_name
        self.user = user
        self.password = password
        self.dump_json_payload = dump_json_payload

        # Handlers
        self.error_handler = ServiceErrorHandler()

    # TODO: make function async
    def submit(
        self,
        endpoint: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """
        Send data to the external component by making HTTP POST request.

        Args:
            endpoint (str): communication endpoint exposed by the service for communication with it through the network
            payload (dict[str, Any]): data being transmitted to the service
            metadata (dict[str, Any]): auxiliary data transmitted to the service (e.g., HTTP language header)

        Returns:
            Any: response data in json-encoded format
        """
        # Try to send an HTTP POST request and get a response
        try:
            # https://requests.readthedocs.io/en/latest/api/#requests.post
            # https://www.w3schools.com/python/ref_requests_post.asp
            return requests.post(
                url=f'{self.base_url}{endpoint}',
                auth=HTTPBasicAuth(self.user, self.password),
                headers=metadata,
                json=json.dumps(payload) if self.dump_json_payload else payload,
                timeout=SOURCE_SYSTEM_TIMEOUT,
            ).json()
        except requests.exceptions.RequestException as req_exp:
            # log external component errors
            logger.exception(
                f'{self.display_name} request error',
            )
            return self.error_handler.generate_error({
                'message': str(req_exp),
                'exception': req_exp,
            })
