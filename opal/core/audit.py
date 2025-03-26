"""This module provides support functionality for the django easy audit system."""

from django.http import HttpRequest

from easyaudit.models import RequestEvent


def update_request_event_query_string(request: HttpRequest, method: str, parameters: list[str]) -> None:
    """Get the request event attached to this request path and update query string with POST arguments.

    Args:
        request: The post request data
        method: Request url method eg 'POST', 'GET', 'PATCH' etc
        parameters: Filter request parameters to be appended to the request event query string

    """
    request_event = RequestEvent.objects.filter(
        url=request.path,
        user=request.user,
        method=method,
    ).order_by('-datetime').first()
    query_string = {}
    for param in parameters:
        query_string[param] = request.POST.get(param, '')

    request_event.query_string = query_string
    request_event.save()
