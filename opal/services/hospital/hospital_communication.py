"""Module providing business logic for the hospital's internal communication (e.g., Opal Integration Engine)."""

from django.conf import settings

from ..general.service_communication import ServiceHTTPCommunicationManager


class SourceSystemHTTPCommunicationManager(ServiceHTTPCommunicationManager):
    """Manager that provides functionality for communication with Opal Integration Engine.

    The manager is responsible only for the HTTP communication and handling any communication-related errors.

    The manager is not responsible for the data content being transferred.
    """

    def __init__(self) -> None:
        """Initialize a source-system-specific ServiceHTTPCommunicationManager."""
        super().__init__(
            base_url=settings.SOURCE_SYSTEM_HOST,
            display_name='Source System',
            user=settings.SOURCE_SYSTEM_USER,
            password=settings.SOURCE_SYSTEM_PASSWORD,
            dump_json_payload=True,
        )
