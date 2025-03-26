"""Module providing API views for the `health_data` app."""
from typing import Any, Dict

from django.db.models import QuerySet

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from opal.patients.models import Patient

from ..models import QuantitySample
from .serializers import QuantitySampleSerializer


class CreateQuantitySampleView(generics.CreateAPIView):
    """
    Create view for `QuantitySample`.

    Supports the creation of one or more instances at the same time by passing a list of dictionaries.
    """

    serializer_class = QuantitySampleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self) -> QuerySet[QuantitySample]:
        """
        Filter the `QuantitySample` queryset by the `patient_id` from the URL path.

        Returns:
            a queryset with `QuantitySamples` belonging to the requested patient
        """
        patient_id = self.kwargs['patient_id']

        return QuantitySample.objects.filter(patient_id=patient_id)

    def get_serializer_context(self) -> Dict[str, Any]:
        """
        Return the serializer context with the patient as extra context.

        Ensures that the patient exists and raises a 404 if not.
        Augments the context with the patient instance determined by the `patient_id` from the URL path.

        Returns:
            the serializer context
        """
        patient_id = self.kwargs['patient_id']

        # ensure that the patient exists
        # done here instead of get_queryset to ensure the check is performed for create()
        patient = generics.get_object_or_404(Patient.objects.all(), pk=patient_id)

        context = super().get_serializer_context()
        context.update({'patient': patient})

        return context

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create one or more new model instances.

        Supports data as dictionary (one) or list of dictionaries (one or more new instances).
        See: https://www.django-rest-framework.org/api-guide/serializers/#customizing-listserializer-behavior

        Args:
            request: the HTTP request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the newly created model instances
        """
        # copied from rest_framework.mixins.CreateModelMixin to better support creation of multiple objects
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
