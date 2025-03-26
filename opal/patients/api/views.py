"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.query import QuerySet
from django.db.utils import DataError
from django.utils import timezone

from rest_framework import serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers import models as caregiver_models
from opal.caregivers.api import serializers as registration_serializers
from opal.users.models import User

from ..models import Patient, Relationship
from .data_validators import RegisterApiValidator


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
            return registration_serializers.RegistrationCodePatientDetailedSerializer

        return registration_serializers.RegistrationCodePatientSerializer


class RegistrationRegisterView(APIView):
    """Registration-register api class."""

    permission_classes = [IsAuthenticated]

    def __init__(self) -> None:
        """Initialize RegistrationRegisterView."""
        self.validator = RegisterApiValidator()

    def get_queryset(self) -> QuerySet[Relationship]:
        """
        Override get_queryset to filter relationship by caregiver code.

        Returns:
            The queryset of Relationship
        """
        code = self.kwargs['code']
        return Relationship.objects.filter(registration_codes__code=code)

    @transaction.atomic
    def post(self, request: Request, code: str) -> Response:  # noqa: C901 WPS210 WPS231
        """
        Handle post requests from `patients/api/`.

        Args:
            request (Request): request data of post api.
            code (str): registration code.

        Raises:
            ValidationError: if registration code is invalid.
            ValidationError: if input register data is invalid.

        Returns:
            Http response with the list of patients for a given caregiver.
        """
        db_error = ''
        relationship = self.get_queryset().get()

        if not relationship:
            raise serializers.ValidationError('Registration code is invalid.')

        register_data, validator_errors = self.validator.is_register_data_valid(request.data)
        if validator_errors:
            raise serializers.ValidationError(detail=validator_errors)

        # update registration code status
        registration_code = caregiver_models.RegistrationCode.objects.get(code=code)
        registration_code.status = caregiver_models.RegistrationCodeStatus.REGISTERED
        registration_code.save()

        # update patient legacy_id
        patient = relationship.patient
        patient.legacy_id = register_data.legacy_id
        try:  # noqa: WPS229
            Patient.full_clean(patient)
            patient.save()
        except ValidationError as exception_patient:
            db_error = str(exception_patient.args)

        # update caregiver
        user = User.objects.get(caregiverprofile=relationship.caregiver)
        user.language = register_data.language
        user.phone_number = register_data.phone_number
        user.email = register_data.email
        user.date_joined = timezone.now()
        user.is_active = True
        try:  # noqa: WPS229
            User.full_clean(user)
            user.save()
        except ValidationError as exception_user:
            db_error = str(exception_user.args)

        caregiver_profile = caregiver_models.CaregiverProfile.objects.get(user=user)

        # insert related security answers
        if caregiver_profile and not db_error:
            for data in register_data.security_answers:
                try:
                    caregiver_models.SecurityAnswer.objects.create(
                        user=caregiver_profile,
                        question=data.question,
                        answer=data.answer,
                    )
                except DataError as exception_answer:
                    db_error = str(exception_answer.args)
                    break

        if db_error:
            transaction.set_rollback(True)
        else:
            db_error = 'Saved the patient data successfully.'

        return Response({'detail': db_error})
