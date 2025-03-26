"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers import models as caregiver_models
from opal.caregivers.api import serializers as caregiver_serializers
from opal.core.drf_permissions import CaregiverPatientPermissions
from opal.patients.api.serializers import CaregiverRelationshipSerializer
from opal.users.models import User

from ..models import Patient, Relationship


class RetrieveRegistrationDetailsView(RetrieveAPIView):
    """Class handling GET requests for registration code values."""

    queryset = (
        caregiver_models.RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).filter(status=caregiver_models.RegistrationCodeStatus.NEW)
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
            return caregiver_serializers.RegistrationCodePatientDetailedSerializer
        return caregiver_serializers.RegistrationCodePatientSerializer


class RegistrationCompletionView(APIView):
    """Registration-register `APIView` class for handling "registration-completed" requests."""

    serializer_class = caregiver_serializers.RegistrationRegisterSerializer

    # TODO
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, code: str) -> Response:  # noqa: C901 WPS210 WPS231
        """
        Handle POST requests from `registration/<str:code>/register/`.

        Args:
            request: REST framework's request object.
            code: registration code.

        Raises:
            ValidationError: validation error.

        Returns:
            HTTP response with the error or success message.
        """
        validation_error = None
        serializer = self.serializer_class(
            data=request.data,
        )
        print(request.data),
        serializer.is_valid(raise_exception=True)
        register_data = serializer.validated_data

        # update registration code status
        registration_code = self._get_and_update_registration_code(code)

        # update patient legacy_id
        try:
            self._update_patient_legacy_id(
                registration_code.relationship.patient,
                register_data['relationship']['patient']['legacy_id'],
            )
        except ValidationError as exception_patient:
            validation_error = str(exception_patient.args)

        # update caregiver
        if not validation_error:
            try:
                self._update_caregiver(
                    registration_code.relationship.caregiver.user,
                    register_data['relationship']['caregiver'],
                )
            except ValidationError as exception_user:
                validation_error = str(exception_user.args)

        # insert related security answers
        if not validation_error:
            caregiver_profile = registration_code.relationship.caregiver
            self._insert_security_answers(
                caregiver_profile,
                register_data['security_answers'],
            )

        if validation_error:
            transaction.set_rollback(True)
            raise serializers.ValidationError({'detail': _(validation_error)})

        return Response()

    def _get_and_update_registration_code(self, code: str) -> caregiver_models.RegistrationCode:
        """
        Get and update RegistrationCode object.

        Args:
            code (str): registration code.

        Returns:
            the object of model RegistrationCode, None if not exists
        """
        registration_code = caregiver_models.RegistrationCode.objects.select_related(
            'relationship__patient',
            'relationship__caregiver__user',
        ).filter(code=code, status=caregiver_models.RegistrationCodeStatus.NEW).get()
        registration_code.status = caregiver_models.RegistrationCodeStatus.REGISTERED
        registration_code.full_clean()
        registration_code.save()
        return registration_code

    def _update_patient_legacy_id(self, patient: Patient, legacy_id: int) -> None:
        """
        Update Patient Legacy_id.

        Args:
            patient: Patient object
            legacy_id: number or None.
        """
        patient.legacy_id = legacy_id
        patient.full_clean()
        patient.save()

    def _update_caregiver(self, user: User, info: dict) -> None:
        """
        Update Patient Legacy_id.

        Args:
            user: User object
            info: Caregiver info to be updated
        """
        user.language = info['user']['language']
        user.phone_number = info['user']['phone_number']
        user.date_joined = timezone.now()
        user.is_active = True
        user.full_clean()
        user.save()

    def _insert_security_answers(
        self,
        caregiver_profile: caregiver_models.CaregiverProfile,
        security_answers: list,
    ) -> None:
        """
        Insert security answers.

        Args:
            caregiver_profile: CaregiverProfile object
            security_answers: list of security answer data
        """
        answers = [caregiver_models.SecurityAnswer(**answer, user=caregiver_profile) for answer in security_answers]
        caregiver_models.SecurityAnswer.objects.bulk_create(answers)


class CaregiverRelationshipView(ListAPIView):
    """REST API `ListAPIView` returning list of caregivers for a given patient."""

    serializer_class = CaregiverRelationshipSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, CaregiverPatientPermissions]

    def get_queryset(self) -> QuerySet[Relationship]:
        """Query set to retrieve list of caregivers for the input patient.

        Returns:
            List of caregiver profiles for a given patient
        """
        return Relationship.objects.select_related(
            'caregiver__user',
        ).filter(
            patient__legacy_id=self.kwargs['legacy_id'],
        )
