"""Module providing API views for the `databank` app."""

from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers

from opal.core.drf_permissions import CreateModelPermissions
from opal.patients.models import Patient
from opal.services.data_processing.deidentification import OpenScienceIdentity, PatientData

from ..models import DatabankConsent
from .serializers import DatabankConsentSerializer


class CreateDatabankConsentView(generics.CreateAPIView):
    """`CreateAPIView` for handling POST requests for the `DatabankConsent` instances."""

    queryset = DatabankConsent.objects.none()
    permission_classes = [CreateModelPermissions]
    serializer_class = DatabankConsentSerializer

    def perform_create(self, serializer: serializers.BaseSerializer[DatabankConsent]) -> None:
        """
        Perform the `DatabankConsent` record creation for a specific patient.

        Ensures that the patient with the given UUID exists.

        Args:
            serializer: the serializer instance to use
        """
        patient = get_object_or_404(Patient, uuid=self.kwargs['uuid'])
        osi_identifiers = PatientData(
            first_name=patient.first_name,
            middle_name=serializer.validated_data['middle_name'],
            last_name=patient.last_name,
            gender=patient.get_sex_display(),
            date_of_birth=str(patient.date_of_birth),
            city_of_birth=serializer.validated_data['city_of_birth'],
        )
        guid = OpenScienceIdentity(osi_identifiers).to_signature()

        # Remove non-model fields before saving
        serializer.validated_data.pop('middle_name', None)
        serializer.validated_data.pop('city_of_birth', None)

        serializer.save(
            patient=patient,
            guid=guid,
        )
