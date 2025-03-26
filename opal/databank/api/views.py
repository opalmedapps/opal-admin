"""Module providing API views for the `databank` app."""
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers

from opal.core.drf_permissions import FullDjangoModelPermissions
from opal.patients.models import Patient

from ..models import DatabankConsent
from .serializers import DatabankConsentSerializer


class CreateDatabankConsentView(generics.CreateAPIView):
    """`CreateAPIView` for handling POST requests for the `DatabankConsent` instances."""

    queryset = DatabankConsent.objects.none()
    # TODO: enforce user having access to this patient only
    # TODO: determine who calls this API
    permission_classes = (FullDjangoModelPermissions,)
    serializer_class = DatabankConsentSerializer

    def perform_create(self, serializer: serializers.BaseSerializer[DatabankConsent]) -> None:
        """
        Perform the `DatabankConsent` record creation for a specific patient.

        Ensures that the patient with the given UUID exists.

        Args:
            serializer: the serializer instance to use
        """
        serializer.save(
            patient=get_object_or_404(Patient, uuid=self.kwargs['uuid']),
        )
