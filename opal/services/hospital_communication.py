"""Module providing business logic for the hospital's internal communicatoin (e.g., Opal Integration Engine)."""

import json
from typing import Any

from django.conf import settings

import requests
from requests.auth import HTTPBasicAuth


class OIEHTTPCommunicationManager:
    """Manager that provides functionality for communication with Opal Integration Engine (OIE).

    The manager is responsible only for the HTTP commnication and handling any communication-related errors.

    The manager is not responsible for the data content being transfarred.
    """

    # TODO: make function async
    def submit(
        self,
        endpoint: str,
        payload: dict[str, Any],
        port: int = 6682,
        metadata: dict[str, Any] = None,
    ) -> Any:
        """Send data to the OIE by making HTTP POST request.

        Args:
            endpoint (str): communication endpoint exposed by the OIE for communication with it through the network
            payload (dict[str, Any]): data being transmitted to the OIE
            port (int): network port number exposed by the OIE
            metadata (dict[str, Any]): auxiliary data transmitted to the OIE (e.g., HTTP language header)

        Returns:
            Any: response data in json-encoded format
        """
        # Try to send an HTTP POST request and get a response
        try:
            # TODO: OIE server should support SSL certificates. This will allow to use `verify=True` that fixes S501
            # https://requests.readthedocs.io/en/latest/api/#requests.post
            # https://www.w3schools.com/python/ref_requests_post.asp
            response = requests.post(
                url='{0}:{1}{2}'.format(settings.OIE_HOST, port, endpoint),
                auth=HTTPBasicAuth(settings.OIE_USER, settings.OIE_PASSWORD),
                headers=metadata,
                json=json.dumps(payload),
                timeout=5,
                verify=False,  # noqa: S501
            )
        except requests.exceptions.RequestException as req_exp:
            return self._generate_error_response({'message': str(req_exp)})

        # Try to return a JSON object of the response content
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as decode_err:
            return self._generate_error_response({'message': str(decode_err)})

    # TODO: make function async
    def fetch(
        self,
        endpoint: str,
        params: dict[str, Any],
        port: int,
        metadata: dict[str, Any],
    ) -> Any:
        """Retrieve data from the OIE by making HTTP GET request.

        Args:
            endpoint (str): communication endpoint exposed by the OIE for communication with it through the network
            params (dict[str, Any]): URL parameters (a.k.a query string)
            port (int): network port number exposed by the OIE
            metadata (dict[str, Any]): auxiliary data transmitted to the OIE (e.g., HTTP language header)

        Returns:
            Any: response data in json-encoded format
        """
        # Try to send an HTTP GET request and get a response
        try:
            # TODO: OIE server should support SSL certificates. This will allow to use `verify=True` that fixes S501
            # https://requests.readthedocs.io/en/latest/api/#requests.get
            # https://www.w3schools.com/python/ref_requests_get.asp
            response = requests.get(
                url='{0}:{1}{2}'.format(settings.OIE_HOST, port, endpoint),
                auth=HTTPBasicAuth(settings.OIE_USER, settings.OIE_PASSWORD),
                headers=metadata,
                params=params,
                timeout=5,
                verify=False,  # noqa: S501
            )
        except requests.exceptions.RequestException as req_exp:
            return self._generate_error_response({'message': str(req_exp)})

        # Try to return a JSON object of the response content
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as decode_err:
            return self._generate_error_response({'message': str(decode_err)})

    def _generate_error_response(
        self,
        response_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            'status': 'error',
            'data': response_data,
        }
