# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing different middlewares for the whole project."""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import resolve, reverse
from django.utils.functional import SimpleLazyObject

from auditlog.cid import set_cid
from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware as _AuditlogMiddleware


class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other than LOGIN_URL.

    Exemptions to this requirement can optionally be specified
    in settings by setting a list of routes that are exempt from authentication (AUTH_EXEMPT_ROUTES).

    The LoginRequiredMiddleware needs to be specified after `AuthenticationMiddleware`
    in `settings.py` under `MIDDLEWARE`.

    Inspired by this discussion: https://stackoverflow.com/q/3214589
    See also: https://docs.djangoproject.com/en/dev/topics/http/middleware/#writing-your-own-middleware
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """
        Initialize the middleware.

        Args:
            get_response: the next `get_response` callable (could be a view or the next middleware)
        """
        self.get_response = get_response
        self.api_root = settings.API_ROOT

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the HTTP request to ensure that the user is authenticated.

        Returns a [django.http.HttpResponseRedirect][] if the user is not authenticated.

        Args:
            request: the HTTP request

        Returns:
            the HTTP response
        """
        if (
            not request.user.is_authenticated
            # ignore API URLs since this is handled by DRF
            and not request.path.startswith(f'/{self.api_root}/')
            and self._resolve_route(request) not in settings.AUTH_EXEMPT_ROUTES
        ):
            redirect_to = f'{reverse(settings.LOGIN_URL)}?next={request.path_info}'

            return HttpResponseRedirect(redirect_to)

        return self.get_response(request)

    def _resolve_route(self, request: HttpRequest) -> str | None:
        """
        Resolve the route of the request to the format namespace:url_name.

        Args:
            request: the HTTP request

        Returns:
            the route name, `None` if the path could not be found
        """
        resolver = resolve(request.path_info)

        route_name = resolver.url_name

        if resolver.namespace:
            route_name = f'{resolver.namespace}:{route_name}'

        return route_name


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
