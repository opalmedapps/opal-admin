"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.query import QuerySet

from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers import models as caregiver_models
from opal.caregivers.api import serializers as caregiver_serializers
from opal.core.drf_permissions import CaregiverSelfPermissions, UpdateModelPermissions

from ..api.serializers import CaregiverRelationshipSerializer, PatientDemographicSerializer
from ..models import Patient, Relationship
from ..utils import insert_security_answers, update_caregiver, update_patient_legacy_id, update_registration_code_status


class RetrieveRegistrationDetailsView(RetrieveAPIView):
    """Class handling GET requests for registration code values."""

    queryset = (
        caregiver_models.RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).filter(
            status=caregiver_models.RegistrationCodeStatus.NEW,
        )
    )

    lookup_url_kwarg = 'code'
    lookup_field = 'code'

    def get_object(self) -> Any:
        """
        Override get_object to filter RegistrationCode by patient date_of_death.

        Raises:
            PermissionDenied: return forbidden error for deceased patients.

        Returns:
            The object of RegistrationCode
        """
        registration_code = super().get_object()
        if registration_code.relationship.patient.date_of_death:
            raise PermissionDenied()
        return registration_code

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

    # TODO Remove or keep permission here
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, code: str) -> Response:
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
        register_data = serializer.validated_data

        registration_code = get_object_or_404(
            caregiver_models.RegistrationCode.objects.select_related(
                'relationship__patient',
                'relationship__caregiver__user',
            ).filter(code=code, status=caregiver_models.RegistrationCodeStatus.NEW),
        )

        try:  # noqa: WPS229

            update_registration_code_status(registration_code)

            update_patient_legacy_id(
                registration_code.relationship.patient,
                register_data['relationship']['patient']['legacy_id'],
            )

            update_caregiver(
                registration_code.relationship.caregiver.user,
                register_data['relationship']['caregiver'],
            )
            caregiver_profile = registration_code.relationship.caregiver
            insert_security_answers(
                caregiver_profile,
                register_data['security_answers'],
            )
        except ValidationError as exception:
            transaction.set_rollback(True)
            raise serializers.ValidationError({'detail': str(exception.args)})

        return Response()


class CaregiverRelationshipView(ListAPIView):
    """REST API `ListAPIView` returning list of caregivers for a given patient."""

    serializer_class = CaregiverRelationshipSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, CaregiverSelfPermissions]

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


class PatientDemographicView(UpdateAPIView):
    """REST API `UpdateAPIView` handling PUT and PATCH requests for patient demographic updates."""

    permission_classes = [IsAuthenticated, UpdateModelPermissions]
    queryset = Patient.objects.prefetch_related(
        'hospital_patients__site',
        'relationships__type',
        'relationships__caregiver__user',
    )
    serializer_class = PatientDemographicSerializer
    pagination_class = None

    def get_object(self) -> Any:
        """Perform a custom lookup for a `Patient` object.

        Since there is no `lookup_url` parameter in the endpoints, the lookup is performed by using the provided `mrns`.

        Returns:
            `Patient` object

        Raises:
            NotFound: if `Patient` record has not be found through the provided `mrns` list of `HospitalPatients`
        """
        # Validate the `MRNs` from input
        serializer = PatientDemographicSerializer(
            data=self.request.data,
            fields=('mrns',),
        )
        serializer.is_valid(raise_exception=True)

        patient = Patient.objects.get_patient_by_site_mrn_list(
            serializer.validated_data.get('mrns'),
        )

        # Raise `NotFound` if `HospitalPatient` queryset is empty
        if not patient:
            raise NotFound(
                '{0} {1}'.format(
                    'Cannot find patient record with the provided MRNs and site codes.',
                    'Make sure that MRN/site code pairs refer to the same patient.',
                ),
            )

        # May raise a permission denied
        self.check_object_permissions(self.request, patient)

        return patient
