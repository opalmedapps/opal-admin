# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module consisting of signals used throughout the project."""

from typing import Any, TYPE_CHECKING

from django.dispatch import receiver

import structlog
from django_structlog import signals

if TYPE_CHECKING:
    from django.http import HttpRequest
    import logging


@receiver(signals.bind_extra_request_metadata)
def bind_app_user(request: HttpRequest, logger: logging.Logger, **kwargs: Any) -> None:
    """
    Binds the username from the app user to the structlog context.

    Args:
        request: The request
        logger: The logger
        kwargs: additional keyword arguments
    """
    if 'Appuserid' in request.headers:
        structlog.contextvars.bind_contextvars(app_user=request.headers.get('Appuserid'))
