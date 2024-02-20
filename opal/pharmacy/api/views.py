"""Module providing API views for the `pharmacy` app."""
#from django.shortcuts import get_object_or_404
from django.db import transaction
from typing import Any
from rest_framework import serializers

from opal.core.api.views import HL7APIView
from opal.core.drf_permissions import IsInterfaceEngine

#from rest_framework.response import Response
#from rest_framework import status
from .serializers import PhysicianPrescriptionOrderSerializer

#from opal.patients.models import Patient


class CreatePharmacyView(HL7APIView):
    """`CreateAPIView` (implemented by the `HL7APIView` superclass) for handling POST requests to create pharmacy data."""

    segments_to_parse = ('PID', 'PV1', 'ORC', 'RXE', 'RXR', 'RXC', 'NTE')
    serializer_class = PhysicianPrescriptionOrderSerializer
    permission_classes = (IsInterfaceEngine,)

    def create(self, request, *args, **kwargs):
        """Extract and transform the parsed data from the request.

        Args:

        Returns:
        """
        transformed_data = self._transform_parsed_to_serializer_structure(request.data)
        serializer = self.get_serializer(data=transformed_data)
        return super().create(request, *args, **kwargs)

    def _transform_parsed_to_serializer_structure(self, parsed_data: dict[str, Any]) -> dict:
        """Transform the parsed defaultdict segment data into the expected structure for the serializer."""
        print(parsed_data['PID'])
        print(parsed_data['PV1'][0])
        print(parsed_data['ORC'][0])
        print(parsed_data['RXE'][0])
        print(parsed_data['RXR'])
        print(parsed_data['RXC'])
        print(parsed_data['NTE'][0])






    # @transaction.atomic
    # def perform_create(self, serializer: serializers.BaseSerializer) -> None:
    #     """
    #     Perform the `PhysicianPrescriptionOrder` creation for a specific patient.

    #     Raises:
    #         ValidationError: If

    #     """

