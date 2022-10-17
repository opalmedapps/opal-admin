"""This module is an API view that returns the encryption value required to handle listener's registration requests."""

import random

from django.db.models.functions import SHA512
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers as drf_serializers, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers.api.serializers import EmailVerificationSerializer, RegistrationEncryptionInfoSerializer
from opal.caregivers.models import EmailVerification, RegistrationCode, RegistrationCodeStatus
from opal.patients.api.serializers import CaregiverPatientSerializer
from opal.patients.models import Relationship


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


class ApiEmailVerificationView(APIView):
    """Class to save and verify the user's email and email verification code."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, code: str) -> Response:
        """
        Handle GET requests from `registration/<str:code>/verify-email-code/`.

        Args:
            request: Http request made by the listener needed to retrive `Appuserid`.
            code (str): registration code.

        Returns:
            Http response with the verification result of the email code.
        """
        registration_code = None
        try:
            registration_code = RegistrationCode.objects.select_related(
                'relationship__caregiver',
            ).prefetch_related(
                'relationship__patient__hospital_patients',
            ).filter(code=code, status=RegistrationCodeStatus.NEW).get()
        except RegistrationCode.DoesNotExist:
            raise drf_serializers.ValidationError({'detail': _('Registration code is invalid')})

        verification_code = request.data['code']
        try:
            registration_code.relationship.caregiver.email_verifications.get(code=verification_code)
        except EmailVerification.DoesNotExist:
            raise drf_serializers.ValidationError({'detail': _('Verification code is invalid')})

        return Response({'detail': 'Email is verified'})

    def post(self, request: Request, code: str) -> Response:
        """
        Handle POST requests from `registration/<str:code>/verify-email/`.

        Args:
            request: Http request made by the listener needed to retrive `Appuserid`.
            code (str): registration code.

        Returns:
            Http response with the result message of the api.
        """
        registration_code = None
        try:
            registration_code = RegistrationCode.objects.select_related(
                'relationship__caregiver',
            ).prefetch_related(
                'relationship__patient__hospital_patients',
            ).filter(code=code, status=RegistrationCodeStatus.NEW).get()
        except RegistrationCode.DoesNotExist:
            raise drf_serializers.ValidationError({'detail': _('Registration code is invalid')})

        input_serializer = EmailVerificationSerializer(data=request.data, fields=('email',), partial=True)
        input_serializer.is_valid(raise_exception=True)

        email = input_serializer.data['email']
        verification_code = random.randint(100000, 999999)
        EmailVerification.objects.create(
            caregiver=registration_code.relationship.caregiver,
            code=verification_code,
            email=email,
            sent_at=timezone.now(),
        )

        return Response()
