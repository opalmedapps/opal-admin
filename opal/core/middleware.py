# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing different middlewares for the whole project."""

from django.http import HttpRequest, HttpResponse
from django.utils.functional import SimpleLazyObject

from auditlog.cid import set_cid
from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware as _AuditlogMiddleware


# source: https://github.com/jazzband/django-auditlog/issues/115#issuecomment-1539262735
class AuditlogMiddleware(_AuditlogMiddleware):
    """Custom middleware for django-auditlog with better support for DRF."""

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the call to this middleware.

        Args:
            request: the HTTP request

        Returns:
            the HTTP response
        """
        remote_addr = self._get_remote_addr(request)
        # make user a lazy object to retrieve API users
        # DRF authenticates in views rather than middlewares like Django does
        user = SimpleLazyObject(lambda: self._get_actor(request))

        set_cid(request)

        with set_actor(actor=user, remote_addr=remote_addr):
            return self.get_response(request)  # type: ignore[no-any-return]
