"""This module is an API view that returns the encryption value required to handle listener's registration requests."""

import random

from django.db.models.functions import SHA512
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers as drf_serializers
from rest_framework import status
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


class ApiVerifyEmailView(APIView):
    """Class to save the user's email and email verification code.

    And send email to the user with the verification code.
    """

    permission_classes = [IsAuthenticated]
    min_number = 100000
    max_number = 999999

    def get_queryset(self) -> QuerySet[RegistrationCode]:
        """
        Override get_queryset to filter RegistrationCode by registration code.

        Returns:
            The queryset of RegistrationCode
        """
        code = self.kwargs.get('code') if hasattr(self, 'kwargs') else None
        return RegistrationCode.objects.select_related(
            'relationship__caregiver',
        ).prefetch_related(
            'relationship__caregiver__email_verifications',
        ).filter(code=code, status=RegistrationCodeStatus.NEW)

    def post(self, request: Request, code: str) -> Response:  # noqa: WPS210
        """
        Handle POST requests from `registration/<str:code>/verify-email/`.

        Args:
            request: Http request made by the listener.
            code: registration code.

        Raises:
            ValidationError: The object not found.

        Returns:
            Http response with empty message.
        """
        registration_code = None
        try:
            registration_code = self.get_queryset().get()
        except RegistrationCode.DoesNotExist:
            raise drf_serializers.ValidationError({'detail': _('Registration code is invalid.')})

        input_serializer = EmailVerificationSerializer(data=request.data, fields=('email',), partial=True)
        input_serializer.is_valid(raise_exception=True)

        email = input_serializer.validated_data['email']
        verification_code = random.randint(self.min_number, self.max_number)  # noqa: S311
        caregiver = registration_code.relationship.caregiver
        try:
            email_verification = registration_code.relationship.caregiver.email_verifications.get(
                email=email,
            )
        except EmailVerification.DoesNotExist:
            email_verification = EmailVerification.objects.create(
                caregiver=caregiver,
                code=verification_code,
                email=email,
                sent_at=timezone.now(),
            )
        else:
            input_serializer.update(
                email_verification,
                {
                    'code': verification_code,
                    'is_verified': False,
                    'sent_at': timezone.now(),
                },
            )

        return Response()


class ApiVerifyEmailCodeView(APIView):
    """Class to verify the user's email with received verification code."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[RegistrationCode]:
        """
        Override get_queryset to filter RegistrationCode by registration code.

        Returns:
            The queryset of RegistrationCode
        """
        code = self.kwargs.get('code') if hasattr(self, 'kwargs') else None
        return RegistrationCode.objects.select_related(
            'relationship__caregiver',
        ).prefetch_related(
            'relationship__caregiver__email_verifications',
        ).filter(code=code, status=RegistrationCodeStatus.NEW)

    def put(self, request: Request, code: str) -> Response:
        """
        Handle PUT requests from `registration/<str:code>/verify-email-code/`.

        Args:
            request: Http request made by the listener.
            code: registration code.

        Raises:
            ValidationError: The object not found.

        Returns:
            Http response with empty message.
        """
        registration_code = None
        try:
            registration_code = self.get_queryset().get()
        except RegistrationCode.DoesNotExist:
            raise drf_serializers.ValidationError({'detail': _('Registration code is invalid.')})

        input_serializer = EmailVerificationSerializer(data=request.data, fields=('code',), partial=True)
        input_serializer.is_valid(raise_exception=True)

        verification_code = input_serializer.validated_data['code']
        try:
            email_verification = registration_code.relationship.caregiver.email_verifications.get(
                code=verification_code,
            )
        except EmailVerification.DoesNotExist:
            raise drf_serializers.ValidationError({'detail': _('Verification code is invalid.')})
        else:
            email_verification.is_verified = True
            email_verification.save()
            user = registration_code.relationship.caregiver.user
            user.email = email_verification.email
            user.save()

        return Response()
