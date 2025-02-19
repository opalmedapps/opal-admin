# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module consisting of signals used throughout the project."""

import logging
from typing import Any

from django.dispatch import receiver
from django.http import HttpRequest

import structlog
from django_structlog import signals


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
