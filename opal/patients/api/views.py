"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers.api.serializers import RegistrationCodePatientDetailedSerializer, RegistrationCodePatientSerializer, RegistrationCodeSerializer
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus
from opal.users.models import User

from ..models import Patient, Relationship
from .serializers import CaregiverPatientSerializer, PatientSerializer, RelationshipSerializer


class RetrieveRegistrationDetailsView(RetrieveAPIView):
    """Class handling GET requests for registration code values."""

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).filter(status=RegistrationCodeStatus.NEW)
    )

    lookup_url_kwarg = 'code'
    lookup_field = 'code'

    def get_serializer_class(self, *args: Any, **kwargs: Any) -> Type[serializers.BaseSerializer]:
        """Override 'get_serializer_class' to switch the serializer based on the GET parameter `detailed`.

        Args:
            args (list): request parameters
            kwargs (dict): request parameters

        Returns:
            The expected serializer according to the request parameter.
        """
        if 'detailed' in self.request.query_params:
            return RegistrationCodePatientDetailedSerializer

        return RegistrationCodePatientSerializer


class RegistrationRegisterView(APIView):
    """Registration-register api class."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Relationship]:
        """
        Override get_queryset to filter relationship by caregiver code.

        Returns:
            The queryset of Relationship
        """
        code = self.kwargs['code']
        return Relationship.objects.filter(registration_codes__code=code)

    def post(self, request: Request, code: str) -> Response:
        """
        Handle post requests from `patients/api/`.

        Args:
            request (Request): request data of post api.

        Returns:
            Http response with the list of patients for a given caregiver.
        """
        # patient = request.data.get('patient')
        # caregiver = request.data.get('caregiver')

        # update caregiver

        # get or create caregiver profile

        # insert or update related security answers
        relationship = self.get_queryset()

        return Response({'data': relationship.get().status})
