"""This module is an API view that returns the encryption value required to handle listener's registration requests."""
from django.db.models.functions import SHA512

from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers.api.serializer import RegistrationEncryptionInfoSerializer
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus
from opal.patients.models import Relationship
from opal.patients.serializer import CaregiverPatientSerializer


class GetRegistrationEncryptionInfoView(RetrieveAPIView):
    """Class handling gets requests for registration encryption values."""

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).annotate(code_sha512=SHA512('code')).filter(status=RegistrationCodeStatus.NEW)
    )
    serializer_class = RegistrationEncryptionInfoSerializer
    lookup_url_kwarg = 'hash'
    lookup_field = 'code_sha512'


class GetCaregiverPatientsList(APIView):
    """Class to return a list of patients for a given caregiver."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Handle GET requests from `caregivers/patients/`.

        Args:
            request: Http request made by the listener needed to retrive `Appuserid`.

        Returns:
            Http response with the list of patients for a given caregiver.
        """
        user_id = request.headers.get('Appuserid')
        if user_id:
            relationships = Relationship.objects.get_patient_list_for_caregiver(user_id)
            response = Response(
                CaregiverPatientSerializer(relationships, many=True).data,
            )
        else:
            response = Response([], status=status.HTTP_400_BAD_REQUEST)

        return response
