"""Module providing API views for the `health_data` app."""
from typing import Any, Dict

from rest_framework import generics, permissions, serializers

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
