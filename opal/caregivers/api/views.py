"""This module is an API view that returns the encryption value required to handle listener's registration requests."""
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.functions import SHA512
from django.db.models.query import QuerySet
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework import serializers as drf_serializers
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers import models as caregiver_models
from opal.caregivers.api import serializers as caregiver_serializers
from opal.caregivers.api.serializers import (
    CaregiverSerializer,
    DeviceSerializer,
    EmailVerificationSerializer,
    RegistrationEncryptionInfoSerializer,
)
from opal.caregivers.models import CaregiverProfile, Device, EmailVerification, RegistrationCode, RegistrationCodeStatus
from opal.core.api.mixins import AllowPUTAsCreateMixin
from opal.core.drf_permissions import IsListener, IsRegistrationListener
from opal.core.utils import generate_random_number
from opal.patients import utils
from opal.patients.api.serializers import CaregiverPatientSerializer
from opal.patients.models import Relationship
from opal.users.models import Caregiver, User

from .. import constants


class GetRegistrationEncryptionInfoView(RetrieveAPIView[RegistrationCode]):
    """Class handling gets requests for registration encryption values."""

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).annotate(code_sha512=SHA512('code')).filter(status=RegistrationCodeStatus.NEW)
    )
    permission_classes = (IsRegistrationListener,)
    serializer_class = RegistrationEncryptionInfoSerializer
    lookup_url_kwarg = 'hash'
    lookup_field = 'code_sha512'


class UpdateDeviceView(AllowPUTAsCreateMixin[Device], UpdateAPIView[Device]):
    """Class handling requests for updates or creations of device ids."""

    permission_classes = (IsListener,)
    serializer_class = DeviceSerializer
    lookup_url_kwarg = 'device_id'
    lookup_field = 'device_id'

    def get_queryset(self) -> QuerySet[Device]:
        """Provide the desired object or fails with 404 error.

        Returns:
            Device object or 404.
        """
        # TODO: filter also by current user (once QSCCD-250 is done)
        # or use Appuserid header
        return Device.objects.filter(device_id=self.kwargs['device_id'])


class GetCaregiverPatientsList(APIView):
    """Class to return a list of patients for a given caregiver."""

    permission_classes = (IsListener,)

    def get(self, request: Request) -> Response:
        """
        Handle GET requests from `caregivers/patients/`.

        Args:
            request: Http request made by the listener needed to retrieve `Appuserid`.

        Raises:
            ParseError: If the caregiver username was not provided.

        Returns:
            Http response with the list of patients for a given caregiver.
        """
        user_id = request.headers.get('Appuserid')

        if not user_id:
            raise exceptions.ParseError(
                "Requests to caregiver APIs must provide a header 'Appuserid' representing the current user.",
            )

        relationships = Relationship.objects.get_patient_list_for_caregiver(user_id)
        return Response(
            CaregiverPatientSerializer(relationships, many=True).data,
        )


class CaregiverProfileView(RetrieveAPIView[CaregiverProfile]):
    """Retrieve the profile of the current caregiver."""

    permission_classes = (IsListener,)
    serializer_class = CaregiverSerializer
    queryset = CaregiverProfile.objects.all().select_related('user')
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle retrieval of a caregiver profile.

        Args:
            request: the HTTP request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the HTTP response

        Raises:
            ParseError: if the Appuserid HTTP header is missing
        """
        user_id = request.headers.get('Appuserid')

        if not user_id:
            raise exceptions.ParseError(
                "Requests to caregiver APIs must provide a header 'Appuserid' representing the current user.",
            )

        # manually set the username kwarg since it is not provided via the URL
        self.kwargs['username'] = user_id

        return super().retrieve(request, *args, **kwargs)


class RetrieveRegistrationCodeMixin:
    """Mixin class that provides `get_queryset()` to lookup a `RegistrationCode` based on a given `code`."""

    kwargs: dict[str, Any]

    def get_queryset(self) -> QuerySet[RegistrationCode]:
        """
        Override get_queryset to filter RegistrationCode by registration code.

        Returns:
            The queryset of RegistrationCode
        """
        code = self.kwargs.get('code') if hasattr(self, 'kwargs') else None
        return RegistrationCode.objects.select_related(
            'relationship__caregiver',
            'relationship__caregiver__user',
        ).prefetch_related(
            'relationship__caregiver__email_verifications',
        ).filter(code=code, status=RegistrationCodeStatus.NEW)


# TODO: replace this with RetrieveAPIView in the future
class VerifyEmailView(RetrieveRegistrationCodeMixin, APIView):
    """View that initiates email verification for a given email address.

    And send email to the user with the verification code.
    """

    permission_classes = (IsRegistrationListener,)

    def post(self, request: Request, code: str) -> Response:  # noqa: WPS210
        """
        Generate a random verification code and set up the EmailVerification instance.

        If the user requested to re-send the code too soon, it fails.

        Args:
            request: the HTTP request.
            code: registration code.

        Raises:
            ValidationError: if re-sending the verification code was requested too soon.

        Returns:
            Http response with empty message.
        """
        registration_code = get_object_or_404(self.get_queryset())

        input_serializer = EmailVerificationSerializer(data=request.data, fields=('email',))
        input_serializer.is_valid(raise_exception=True)

        email = input_serializer.validated_data['email']
        #  Check whether the email is already registered
        if Caregiver.objects.filter(email=email).exists():
            raise drf_serializers.ValidationError(
                _('The email is already registered.'),
            )

        verification_code = generate_random_number(constants.VERIFICATION_CODE_LENGTH)
        caregiver_profile = registration_code.relationship.caregiver
        try:
            email_verification = caregiver_profile.email_verifications.get(
                email=email,
            )
        except EmailVerification.DoesNotExist:
            email_verification = EmailVerification.objects.create(
                caregiver=caregiver_profile,
                code=verification_code,
                email=email,
                sent_at=timezone.now(),
            )
            self._send_verification_code_email(email_verification, caregiver_profile.user)
        else:
            # in case there is an error sent_at is None, but wont happen in fact
            time_delta = timezone.now() - timezone.localtime(email_verification.sent_at)
            if time_delta.total_seconds() > constants.TIME_DELAY:
                input_serializer.update(
                    email_verification,
                    {
                        'code': verification_code,
                        'is_verified': False,
                        'sent_at': timezone.now(),
                    },
                )
                self._send_verification_code_email(email_verification, caregiver_profile.user)
            else:
                raise drf_serializers.ValidationError(
                    _('Please wait 10 seconds before requesting a new verification code.'),
                )

        return Response()

    def _send_verification_code_email(
        self,
        email_verification: EmailVerification,
        user: User,
    ) -> None:
        """
        Send verification email to the user with an template according to the user language.

        Args:
            email_verification: object EmailVerification
            user: object User
        """
        context = {
            'code': email_verification.code,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

        email_plain = render_to_string(
            'email/verification_code.txt',
            context,
        )
        email_html = render_to_string(
            'email/verification_code.html',
            context,
        )

        send_mail(
            _('Opal Verification Code'),
            email_plain,
            settings.EMAIL_FROM_REGISTRATION,
            [email_verification.email],
            html_message=email_html,
        )


# TODO: replace this with RetrieveAPIView in the future
class VerifyEmailCodeView(RetrieveRegistrationCodeMixin, APIView):
    """View that verifies the user-provided verification code with the actual one."""

    permission_classes = (IsRegistrationListener,)

    def post(self, request: Request, code: str) -> Response:
        """
        Verify that the provided code matches the expected one.

        And if so, it deletes the EmailVerification,
        and updates the email on the user instance with the verified one.

        Args:
            request: the HTTP request.
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
            is_verified=False,
        )

        email_verification.is_verified = True
        email_verification.save()

        return Response()


class RegistrationCompletionView(APIView):
    """Registration-register `APIView` class for handling "registration-completed" requests."""

    serializer_class = caregiver_serializers.RegistrationRegisterSerializer
    permission_classes = (IsRegistrationListener,)

    @transaction.atomic
    def post(self, request: Request, code: str) -> Response:  # noqa: WPS210 (too many local variables)
        """
        Handle POST requests from `registration/<str:code>/register/`.

        Args:
            request: REST framework's request object.
            code: registration code.

        Raises:
            ValidationError: validation error.

        Returns:
            HTTP response with the error or success status.
        """
        serializer = self.serializer_class(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        registration_code = get_object_or_404(
            caregiver_models.RegistrationCode.objects.select_related(
                'relationship__patient',
                'relationship__caregiver__user',
            ).filter(code=code, status=caregiver_models.RegistrationCodeStatus.NEW),
        )
        caregiver_data = validated_data['relationship']['caregiver']
        existing_caregiver = utils.find_caregiver(caregiver_data['user']['username'])
        relationship = registration_code.relationship

        try:  # noqa: WPS229
            utils.update_registration_code_status(registration_code)
            utils.update_patient_legacy_id(relationship.patient, validated_data['relationship']['patient']['legacy_id'])

            if existing_caregiver:
                utils.replace_caregiver(existing_caregiver, relationship)
            else:
                self._handle_new_caregiver(relationship, caregiver_data)
                utils.insert_security_answers(relationship.caregiver, validated_data['security_answers'])
        except ValidationError as exception:
            transaction.set_rollback(True)
            raise serializers.ValidationError({'detail': str(exception.args)})

        return Response()

    def _handle_new_caregiver(self, relationship: Relationship, caregiver_data: dict[str, Any]) -> None:
        """
        Handle registration completion for a new caregiver.

        Args:
            relationship: the relationship
            caregiver_data: the validated registration data for the caregiver

        Raises:
            ValidationError: if the caregiver is already registered or there is no verified email
        """
        # a user can potentially verify multiple email address during the same process
        # use the last one
        email_verification = relationship.caregiver.email_verifications.filter(
            is_verified=True,
        ).order_by('-sent_at').first()

        if not email_verification:
            raise drf_serializers.ValidationError('Caregiver email is not verified.')

        self._update_caregiver(relationship.caregiver, email_verification.email, caregiver_data)

    def _update_caregiver(
        self,
        caregiver_profile: caregiver_models.CaregiverProfile,
        email: str,
        caregiver_data: dict[str, Any],
    ) -> None:
        """
        Update the caregiver with the provided data.

        Args:
            caregiver_profile: the caregiver profile instance to update
            email: the verified email
            caregiver_data: the validated data specific to the caregiver
        """
        user_data = caregiver_data['user']
        utils.update_caregiver(
            caregiver_profile.user,
            email,
            user_data['username'],
            user_data['language'],
            user_data['phone_number'],
        )
        utils.update_caregiver_profile(
            caregiver_profile,
            caregiver_data['legacy_id'],
        )
