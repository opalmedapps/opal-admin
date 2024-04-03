"""Module providing different middlewares for the whole project."""
from collections.abc import Callable
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import resolve, reverse


class LoginRequiredMiddleware():
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
        """Initialize the middleware.

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
            and not request.path.startswith('/{api_root}/'.format(api_root=self.api_root))
            and self._resolve_route(request) not in settings.AUTH_EXEMPT_ROUTES
        ):
            redirect_to = '{login_url}?next={next_url}'.format(
                login_url=reverse(settings.LOGIN_URL),
                next_url=request.path_info,
            )

            return HttpResponseRedirect(redirect_to)

        return self.get_response(request)

    def _resolve_route(self, request: HttpRequest) -> Optional[str]:
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
            route_name = '{namespace}:{url_name}'.format(namespace=resolver.namespace, url_name=route_name)

        return route_name
