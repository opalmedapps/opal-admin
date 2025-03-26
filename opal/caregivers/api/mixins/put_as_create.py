"""
Custom mixin allows for creation, update, and partial update from a single class mixin.

In general, a view inheriting this mixin should specify:
    permission_classes
    serializer_class
    lookup_url_kwarg
    lookup_field

    put/patch methods which call self.update and self.partial_update respectively

    get_queryset: return the targetted model object using the keyword args or request data

"""
from typing import Any

from django.http import Http404

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request, clone_request
from rest_framework.response import Response


class AllowPUTAsCreateMixin(GenericAPIView):
    """The following mixin class may be used in order to update or create records in the targeted model."""

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # noqa: WPS210
        """Update the targetted model or create if it doesn't exist.

        Args:
            request (Request): request object with parameters to update or create
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            HTTP `Response` success or failure
        """
        partial = kwargs.pop('partial', False)
        instance = self._get_object_or_none()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if instance is None:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            lookup_value = self.kwargs[lookup_url_kwarg]
            extra_kwargs = {self.lookup_field: lookup_value}
            serializer.save(**extra_kwargs)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Set partial parameter and re-call update method.

        Args:
            request (Request): request object with parameters to update or create
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            self.update()
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def _get_object_or_none(self) -> Any:
        """Attempt to retrieve object.

        If not found we use clone_request to check if the caller has the required permissions for a POST request.

        Returns:
            Device object, 404, or clone_request with POST action.

        Raises:
            Http404: the device is not found.

        """
        try:
            return self.get_object()
        except Http404:
            if self.request.method == 'PUT':
                # For PUT-as-create operation, we need to ensure that we have
                # relevant permissions, as if this was a POST request.  This
                # will either raise a PermissionDenied exception, or simply
                # return None.
                self.check_permissions(clone_request(self.request, 'POST'))
            else:
                # PATCH requests where the object does not exist should still
                # return a 404 response.
                raise
