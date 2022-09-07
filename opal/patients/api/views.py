"""This module is an API view that returns the patient detaild and non-detailed info via registration code."""

from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.patients.api.serializer import RegistrationCodePatientSerializer
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus


class PatientRetieveView(RetrieveAPIView):
    """Class handling gets requests for registration code values."""

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).select_related(
            'relationship__patient__hospital_patient__site_institution',
        ).filter(status=RegistrationCodeStatus.NEW)
    )
    serializer_class = RegistrationCodePatientSerializer
    lookup_url_kwarg = 'code'
    lookup_field = 'code'
