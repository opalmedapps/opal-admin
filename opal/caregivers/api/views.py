"""This module is an API view that returns the encryption value required to handle listener's registration requests."""
from django.db.models.functions import SHA512
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers.api.serializers import EmailVerificationSerializer, RegistrationEncryptionInfoSerializer
from opal.caregivers.models import EmailVerification, RegistrationCode, RegistrationCodeStatus
from opal.core.utils import generate_random_number
from opal.patients.api.serializers import CaregiverPatientSerializer
from opal.patients.models import Relationship

from .. import constants


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


class RetrieveRegistrationCodeMixin(APIView):
    """Mixin class that provides `get_queryset()` to lookup a `RegistrationCode` based on a given `code`."""

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


class VerifyEmailView(RetrieveRegistrationCodeMixin, APIView):
    """View that initiates email verification for a given email address.

    And send email to the user with the verification code.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, code: str) -> Response:  # noqa: WPS210
        """
        Generate a random verification code and set up the EmailVerification instance.

        If the user requested to re-send the code too soon, it fails.

        Args:
            request: Http request made by the listener.
            code: registration code.

        Raises:
            ValidationError: resend email after 10 seconds.

        Returns:
            Http response with empty message.
        """
        registration_code = get_object_or_404(self.get_queryset())

        input_serializer = EmailVerificationSerializer(data=request.data, fields=('email',))
        input_serializer.is_valid(raise_exception=True)

        email = input_serializer.validated_data['email']
        verification_code = generate_random_number(constants.VERIFICATION_CODE_LENGTH)
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
            # in case there is an error sent_at is None, but wont happen in fact
            time_delta = timezone.now() - timezone.localtime(email_verification.sent_at)
            if time_delta.total_seconds() >= constants.TIME_DELAY:
                input_serializer.update(
                    email_verification,
                    {
                        'code': verification_code,
                        'is_verified': False,
                        'sent_at': timezone.now(),
                    },
                )
            else:
                raise drf_serializers.ValidationError(
                    _('Please wait 10 seconds before requesting a new verification code.'),
                )

        return Response()


class VerifyEmailCodeView(RetrieveRegistrationCodeMixin, APIView):
    """View that verifies the user-provided verification code with the actual one."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, code: str) -> Response:  # noqa: WPS210
        """
        Verify that the provided code matches the expected one.

        And if so, it deletes the EmailVerification,
        and updates the email on the user instance with the verified one.

        Args:
            request: Http request made by the listener.
            code: registration code.

        Returns:
            Http response with empty message.
        """
        registration_code = get_object_or_404(self.get_queryset())

        input_serializer = EmailVerificationSerializer(data=request.data, fields=('code', 'email'))
        input_serializer.is_valid(raise_exception=True)

        verification_code = input_serializer.validated_data['code']
        email = input_serializer.validated_data['email']

        email_verification = get_object_or_404(
            registration_code.relationship.caregiver.email_verifications,
            code=verification_code,
            email=email,
        )

        email_verification.delete()
        user = registration_code.relationship.caregiver.user
        user.email = email_verification.email
        user.save()

        return Response()
