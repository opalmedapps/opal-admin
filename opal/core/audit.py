"""This module provides support functionality for the django easy audit system."""

from django.http import HttpRequest

from easyaudit.models import RequestEvent


<<<<<<< HEAD
def update_request_event_query_string(request: HttpRequest, parameters: list[str]) -> None:
=======
def update_request_event_query_string(request: HttpRequest, method: str, parameters: list[str]) -> None:
>>>>>>> 22712f3 (fast forward assembly)
    """Get the request event attached to this request path and update query string with POST arguments.

    Args:
        request: The post request data
<<<<<<< HEAD
=======
        method: Request url method eg 'POST', 'GET', 'PATCH' etc
>>>>>>> 22712f3 (fast forward assembly)
        parameters: Filter request parameters to be appended to the request event query string

    """
    request_event = RequestEvent.objects.filter(
        url=request.path,
        user=request.user,
<<<<<<< HEAD
=======
        method=method,
>>>>>>> 22712f3 (fast forward assembly)
    ).order_by('-datetime').first()
    query_string = {}
    for param in parameters:
        query_string[param] = request.POST.get(param, '')

    request_event.query_string += str(query_string)
    request_event.save()
