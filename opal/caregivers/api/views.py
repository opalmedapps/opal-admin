"""This module is an API view that return the encryption value required to handle registration listener's requests."""
from django.db.models.functions import SHA512
from django.http import HttpRequest, HttpResponse

from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
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
    """Class to return a list of patient for a given caregiver."""

    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle GET requests from `caregivers/patients/`.

        Args:
            request: Http request made by the listener needed to retrive `Appuserid`.

        Returns:
            Http response with the list of patient for a given caregiver.
        """
        relationships = Relationship.objects.prefetch_related(
            'patient',
            'caregiver',
        ).filter(
            caregiver__user__username=request.headers['Appuserid'],
        ).exclude(
            type__name='Self',
        )
        return Response(
            CaregiverPatientSerializer(relationships, many=True).data,
        )
