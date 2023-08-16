"""Module providing business logic for communication with an external component."""

import json
import logging
from typing import Any, Optional

import requests
from requests.auth import HTTPBasicAuth

from .service_error import ServiceErrorHandler

# add this in any module that need to log
logger = logging.getLogger(__name__)


class ServiceHTTPCommunicationManager:
    """Manager that provides functionality for communication with an external component.

    The manager is responsible only for the HTTP communication and handling any communication-related errors.

    The manager is not responsible for the data content being transferred.
    """
    base_url = ''
    display_name = ''
    user = ''
    password = ''

    def __init__(self) -> None:
        """Initialize helper services."""
        self.error_handler = ServiceErrorHandler()

    # TODO: make function async
    def submit(
        self,
        endpoint: str,
        payload: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Send data to the external component by making HTTP POST request.

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
                url='{0}{1}'.format(self.base_url, endpoint),
                auth=HTTPBasicAuth(self.user, self.password),
                headers=metadata,
                json=json.dumps(payload),
                timeout=5,
            ).json()
        except requests.exceptions.RequestException as req_exp:
            # log external component errors
            logger.exception(
                '{component_name} error: {error_message}'.format(
                    component_name=self.display_name,
                    error_message=str(req_exp),
                ),
            )
            return self.error_handler.generate_error({
                'message': str(req_exp),
                'exception': req_exp,
            })

    # TODO: make function async
    def fetch(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Retrieve data from the external component by making HTTP GET request.

        Args:
            endpoint (str): communication endpoint exposed by the external component for communication with it through the network
            params (dict[str, Any]): URL parameters (a.k.a query string)
            metadata (dict[str, Any]): auxiliary data transmitted to the external component (e.g., HTTP language header)

        Returns:
            Any: response data in json-encoded format
        """
        # Try to send an HTTP GET request and get a response
        try:
            # https://requests.readthedocs.io/en/latest/api/#requests.get
            # https://www.w3schools.com/python/ref_requests_get.asp
            return requests.get(
                url='{0}{1}'.format(self.base_url, endpoint),
                auth=HTTPBasicAuth(self.user, self.password),
                headers=metadata,
                params=params,
                timeout=5,
            ).json()
        except requests.exceptions.RequestException as req_exp:
            return self.error_handler.generate_error({'message': str(req_exp)})
