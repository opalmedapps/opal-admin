"""This module is an API view that returns the encryption value required to handle listener's registration requests."""

import random

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.functions import SHA512
from django.db.models.query import QuerySet
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import get_language_from_request
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
from opal.users.models import User


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
    min_number = 100000
    max_number = 999999

    def get_queryset(self) -> QuerySet[RegistrationCode]:
        """
        Override get_queryset to filter RegistrationCode by registration code.

        Returns:
            The queryset of RegistrationCode
        """
        code = self.kwargs['code']
        return RegistrationCode.objects.select_related(
            'relationship__caregiver',
            'relationship__caregiver__user',
        ).prefetch_related(
            'relationship__caregiver__email_verifications',
        ).filter(code=code, status=RegistrationCodeStatus.NEW)

    def put(self, request: Request, code: str) -> Response:
        """
        Handle GET requests from `registration/<str:code>/verify-email-code/`.

        Args:
            request: Http request made by the listener needed to retrive `Appuserid`.
            code: registration code.

        Raises:
            ValidationError: The object not found.

        Returns:
            Http response with the verification result of the email code.
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

    def post(self, request: Request, code: str) -> Response:  # noqa: WPS210
        """
        Handle POST requests from `registration/<str:code>/verify-email/`.

        Args:
            request: Http request made by the listener needed to retrive `Appuserid`.
            code: registration code.

        Raises:
            ValidationError: The object not found.

        Returns:
            Http response with the result message of the api.
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
        language = get_language_from_request(request)  # type: ignore[arg-type]
        self._send_email(email_verification, caregiver.user, language)
        return Response()

    def _send_email(
        self,
        email_verification: EmailVerification,
        user: User,
        language: str,
    ) -> None:
        """
        Send verification email to the user with an template according to the user language.

        Args:
            email_verification: object EmailVerification.
            user: object User.
            language: language code from the request data.
        """
        email_subject = _('Opal Verification Code')

        template_plain = 'email/verification_code_{0}.txt'.format(language)
        msg_plain = render_to_string(
            template_plain,
            {
                'code': email_verification.code,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
        )
        template_html = 'email/verification_code_{0}.html'.format(language)
        msg_html = render_to_string(
            template_html,
            {
                'code': email_verification.code,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
        )
        send_mail(
            email_subject,
            msg_plain,
            settings.EMAIL_HOST_USER,
            [email_verification.email],
            html_message=msg_html,
        )
