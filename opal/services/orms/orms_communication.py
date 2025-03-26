"""Module providing business logic for communication with ORMS."""
from django.conf import settings

from ..general.service_communication import ServiceHTTPCommunicationManager


class ORMSHTTPCommunicationManager(ServiceHTTPCommunicationManager):
    """Manager that provides functionality for communication with the Opal Room Management System (ORMS).

    The manager is responsible only for the HTTP communication and handling any communication-related errors.

    The manager is not responsible for the data content being transferred.
    """

    base_url = settings.ORMS_HOST
    display_name = 'ORMS'
    user = settings.ORMS_USER
    password = settings.ORMS_PASSWORD
