"""Module providing API views for the `health_data` app."""
from typing import Any

from rest_framework import generics, serializers
from rest_framework.request import Request
from rest_framework.response import Response

from opal.core.drf_permissions import IsListener
from opal.patients.models import Patient

from ..models import QuantitySample
from .serializers import QuantitySampleSerializer


class CreateQuantitySampleView(generics.CreateAPIView):
    """
    Create view for `QuantitySample`.

    Supports the creation of one or more instances at the same time by passing a list of dictionaries.
    """

    serializer_class = QuantitySampleSerializer
    # TODO: change in the future to limit to user with access to the patient
    permission_classes = (IsListener,)

    def get_serializer(self, *args: Any, **kwargs: Any) -> serializers.BaseSerializer[QuantitySample]:
        """
        Return the serializer for this API view.

        Sets the serializers `many` argument to `True` if a list is passed as the data.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the serializer instance
        """
        # support multiple elements
        # see: https://www.django-rest-framework.org/api-guide/serializers/#customizing-listserializer-behavior
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create one or more new quantity samples.

        Ensures that the patient with the uuid as part of the URL exists.
        Raises a 404 if the patient does not exist.

        Args:
            request: the API request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the response
        """
        uuid = self.kwargs['uuid']
        self.patient = generics.get_object_or_404(Patient.objects.all(), uuid=uuid)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer: serializers.BaseSerializer[QuantitySample]) -> None:
        """
        Perform the creation.

        Uses the patient instance determined according to the ID in the URL.

        Args:
            serializer: the serializer instance to use
        """
        serializer.save(patient=self.patient)
