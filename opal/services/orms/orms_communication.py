# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing business logic for communication with ORMS."""

from django.conf import settings

from ..general.service_communication import ServiceHTTPCommunicationManager


class ORMSHTTPCommunicationManager(ServiceHTTPCommunicationManager):
    """
    Manager that provides functionality for communication with the Opal Room Management System (ORMS).

    The manager is responsible only for the HTTP communication and handling any communication-related errors.

    The manager is not responsible for the data content being transferred.
    """

    def __init__(self) -> None:
        """Initialize an ORMS-specific ServiceHTTPCommunicationManager."""
        super().__init__(
            base_url=settings.ORMS_HOST,
            display_name='ORMS',
            user='',
            password='',
            dump_json_payload=False,
        )
