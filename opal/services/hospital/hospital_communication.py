"""Module providing business logic for the hospital's internal communication (e.g., Opal Integration Engine)."""

import json
import logging
from typing import Any, Optional

from django.conf import settings

import requests
from requests.auth import HTTPBasicAuth

from .hospital_error import OIEErrorHandler

# add this in any module that need to log
logger = logging.getLogger(__name__)


class OIEHTTPCommunicationManager:
    """Manager that provides functionality for communication with Opal Integration Engine (OIE).

    The manager is responsible only for the HTTP communication and handling any communication-related errors.

    The manager is not responsible for the data content being transferred.
    """

    def __init__(self) -> None:
        """Initialize helper services."""
        self.error_handler = OIEErrorHandler()

    # TODO: make function async
    def submit(
        self,
        endpoint: str,
        payload: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Send data to the OIE by making HTTP POST request.

        Args:
            endpoint (str): communication endpoint exposed by the OIE for communication with it through the network
            payload (dict[str, Any]): data being transmitted to the OIE
            metadata (dict[str, Any]): auxiliary data transmitted to the OIE (e.g., HTTP language header)

        Returns:
            Any: response data in json-encoded format
        """
        # Try to send an HTTP POST request and get a response
        try:
            # https://requests.readthedocs.io/en/latest/api/#requests.post
            # https://www.w3schools.com/python/ref_requests_post.asp
            return requests.post(
                url='{0}{1}'.format(settings.OIE_HOST, endpoint),
                auth=HTTPBasicAuth(settings.OIE_USER, settings.OIE_PASSWORD),
                headers=metadata,
                json=json.dumps(payload),
                timeout=5,
            ).json()
        except requests.exceptions.RequestException as req_exp:
            # log OIE errors
            logger.exception(
                'OIE error: {oie_message}'.format(
                    oie_message=str(req_exp),
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
        """Retrieve data from the OIE by making HTTP GET request.

        Args:
            endpoint (str): communication endpoint exposed by the OIE for communication with it through the network
            params (dict[str, Any]): URL parameters (a.k.a query string)
            metadata (dict[str, Any]): auxiliary data transmitted to the OIE (e.g., HTTP language header)

        Returns:
            Any: response data in json-encoded format
        """
        # Try to send an HTTP GET request and get a response
        try:
            # https://requests.readthedocs.io/en/latest/api/#requests.get
            # https://www.w3schools.com/python/ref_requests_get.asp
            return requests.get(
                url='{0}{1}'.format(settings.OIE_HOST, endpoint),
                auth=HTTPBasicAuth(settings.OIE_USER, settings.OIE_PASSWORD),
                headers=metadata,
                params=params,
                timeout=5,
            ).json()
        except requests.exceptions.RequestException as req_exp:
            return self.error_handler.generate_error({'message': str(req_exp)})
