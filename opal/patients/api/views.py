"""This module is an API view that returns the patient detaild and non-detailed info via registration code."""

from typing import Any
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.patients.api.serializer import RegistrationCodePatientSerializer, RegistrationCodePatientDetailedSerializer
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus


class PatientRetieveView(RetrieveAPIView):
    """Class handling gets requests for registration code values."""

    queryset = (
        RegistrationCode.objects.filter(status=RegistrationCodeStatus.NEW)
    )

    lookup_url_kwarg = 'code'
    lookup_field = 'code'

    def get_serializer_class(self, *args: Any, **kwargs: Any) -> Any:
        if 'detailed' in self.request.query_params:
            return RegistrationCodePatientDetailedSerializer

        return RegistrationCodePatientSerializer
