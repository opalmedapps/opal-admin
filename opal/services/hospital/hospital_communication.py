"""Module providing business logic for the hospital's internal communication (e.g., Opal Integration Engine)."""

from django.conf import settings

from ..general.service_communication import ServiceHTTPCommunicationManager


class OIEHTTPCommunicationManager(ServiceHTTPCommunicationManager):
    """Manager that provides functionality for communication with Opal Integration Engine (OIE).

    The manager is responsible only for the HTTP communication and handling any communication-related errors.

    The manager is not responsible for the data content being transferred.
    """

    def __init__(self) -> None:
        """Initialize an OIE-specific ServiceHTTPCommunicationManager."""
        super().__init__(
            base_url=settings.OIE_HOST,
            display_name='OIE',
            user=settings.OIE_USER,
            password=settings.OIE_PASSWORD,
            dump_json_payload=True,
        )
