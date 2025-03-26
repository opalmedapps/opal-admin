"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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

    serializer_class = caregiver_serializers.RegistrationRegisterSerializer

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, code: str) -> Response:  # noqa: C901 WPS210 WPS231
        """
        Handle post requests from `patients/api/`.

        Args:
            request (Request): request data of post api.
            code (str): registration code.

        Raises:
            ValidationError: db error.

        Returns:
            Http response with the error or success message.
        """
        db_error = None
        request_serializer = self.serializer_class(
            data=request.data,
            partial=True,
        )
        request_serializer.is_valid(raise_exception=True)
        register_data = request_serializer.data

        # update registration code status
        registration_code = None
        try:
            registration_code = self._get_and_update_regiatration_code(code)
        except caregiver_models.RegistrationCode.DoesNotExist:
            db_error = 'Registration code is invalid.'

        # update patient legacy_id
        if not db_error:
            db_error = self._update_patient_legacy_id(
                registration_code.relationship.patient,
                register_data['patient']['legacy_id'],
            )

        # update caregiver
        if not db_error:
            db_error = self._update_caregiver(
                registration_code.relationship.caregiver.user,
                register_data['caregiver'],
            )

        # insert related security answers
        if not db_error:
            caregiver_profile = registration_code.relationship.caregiver
            self._insert_security_answers(
                caregiver_profile,
                register_data['security_answers'],
            )

        if db_error:
            transaction.set_rollback(True)
            raise serializers.ValidationError({'detail': _(db_error)})

        return Response({'detail': 'Saved the patient data successfully.'})

    def _get_and_update_regiatration_code(self, code: str) -> caregiver_models.RegistrationCode:
        """
        Get and update RegistrationCode object.

        Args:
            code (str): registration code.

        Returns:
            the object of model RegistrationCode, None if not exists
        """
        registration_code = caregiver_models.RegistrationCode.objects.select_related(
            'relationship__patient',
            'relationship__caregiver',
        ).filter(code=code, status=caregiver_models.RegistrationCodeStatus.NEW).get()
        registration_code.status = caregiver_models.RegistrationCodeStatus.REGISTERED
        registration_code.save()
        return registration_code

    def _update_patient_legacy_id(self, patient: Patient, legacy_id: Any) -> str:
        """
        Update Patient Legacy_id.

        Args:
            patient (Patient): Patient object
            legacy_id (Any): number or None.

        Returns:
            The error message string if there is an exception, otherwise return None
        """
        patient.legacy_id = legacy_id
        db_error = ''
        try:
            Patient.full_clean(patient)
        except ValidationError as exception_patient:
            db_error = str(exception_patient.args)
        else:
            patient.save()
        return db_error

    def _update_caregiver(self, user: User, info: dict) -> str:
        """
        Update Patient Legacy_id.

        Args:
            user (User): User object
            info (dict): Caregiver info to be updated

        Returns:
            The error message string if there is an exception, otherwise return None
        """
        user.language = info['language']
        user.phone_number = info['phone_number']
        user.email = info['email']
        user.date_joined = timezone.now()
        user.is_active = True
        db_error = ''
        try:
            User.full_clean(user)

        except ValidationError as exception_user:
            db_error = str(exception_user.args)
        else:
            user.save()
        return db_error

    def _insert_security_answers(
        self,
        caregiver_profile: caregiver_models.CaregiverProfile,
        security_answers: list,
    ) -> None:
        """
        Insert security answers.

        Args:
            caregiver_profile (CaregiverProfile): CaregiverProfile object
            security_answers (list): list of security answer data
        """
        for answer in security_answers:
            caregiver_models.SecurityAnswer.objects.create(
                user=caregiver_profile,
                question=answer['question'],
                answer=answer['answer'],
            )
