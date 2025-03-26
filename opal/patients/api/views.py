"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import DataError
from django.utils import timezone

from rest_framework import serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers import models as caregiver_models
from opal.caregivers.api import serializers as caregiver_serializers
from opal.users.models import User

from ..models import Patient


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


class RegistrationRegisterView(APIView):
    """Registration-register api class."""

    queryset = (
        caregiver_models.RegistrationCode.objects.select_related(
            'relationship__patient',
            'relationship__caregiver',
        ).filter(status=caregiver_models.RegistrationCodeStatus.NEW)
    )
    serializer_class = caregiver_serializers.RegistrationRegisterSerializer
    lookup_url_kwarg = 'code'
    lookup_field = 'code'

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, code: str) -> Response:  # noqa: C901 WPS210 WPS231
        """
        Handle post requests from `patients/api/`.

        Args:
            request (Request): request data of post api.
            code (str): registration code.

        Returns:
            Http response with the error or success message.
        """
        db_error = ''
        request_serializer = self.serializer_class(
            data=request.data,
            partial=True,
        )
        request_serializer.is_valid(raise_exception=True)
        register_data = request_serializer.data

        # update registration code status
        registration_code = self.queryset.get()
        registration_code.status = caregiver_models.RegistrationCodeStatus.REGISTERED
        registration_code.save()

        # update patient legacy_id
        patient = Patient.objects.get(relationships=registration_code.relationship)
        patient.legacy_id = register_data['patient']['legacy_id']
        try:  # noqa: WPS229
            Patient.full_clean(patient)
            patient.save()
        except ValidationError as exception_patient:
            db_error = str(exception_patient.args)

        # update caregiver
        user = User.objects.get(caregiverprofile__relationships=registration_code.relationship)
        user.language = register_data['caregiver']['language']
        user.phone_number = register_data['caregiver']['phone_number']
        user.email = register_data['caregiver']['email']
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
            for data in register_data['caregiver']['security_answers']:
                try:
                    caregiver_models.SecurityAnswer.objects.create(
                        user=caregiver_profile,
                        question=data['question'],
                        answer=data['answer'],
                    )
                except DataError as exception_answer:
                    db_error = str(exception_answer.args)
                    break

        if db_error:
            transaction.set_rollback(True)
        else:
            db_error = 'Saved the patient data successfully.'

        return Response({'detail': db_error})
