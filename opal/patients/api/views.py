"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models.query import QuerySet

from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from opal.caregivers import models as caregiver_models
from opal.caregivers.api import serializers as caregiver_serializers
from opal.core.drf_permissions import CaregiverSelfPermissions, CustomDjangoModelPermissions, UpdateModelPermissions

from .. import utils
from ..api.serializers import (
    CaregiverRelationshipSerializer,
    HospitalPatientSerializer,
    PatientDemographicSerializer,
    PatientSerializer,
)
from ..models import Patient, Relationship


class RetrieveRegistrationDetailsView(RetrieveAPIView):
    """Class handling GET requests for registration code values."""

    queryset = (
        caregiver_models.RegistrationCode.objects.select_related(
            'relationship',
            'relationship__type',
            'relationship__patient',
            'relationship__caregiver',
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
            utils.update_registration_code_status(registration_code)

            utils.update_patient_legacy_id(
                registration_code.relationship.patient,
                register_data['relationship']['patient']['legacy_id'],
            )

            existing_caregiver = utils.find_caregiver(register_data['relationship']['caregiver']['user']['username'])

            if existing_caregiver:
                utils.replace_caregiver(existing_caregiver, registration_code.relationship)
            else:
                utils.update_caregiver(
                    registration_code.relationship.caregiver.user,
                    register_data['relationship']['caregiver'],
                )
                utils.update_caregiver_profile(
                    registration_code.relationship.caregiver,
                    register_data['relationship']['caregiver'],
                )

            caregiver_profile = registration_code.relationship.caregiver
            utils.insert_security_answers(
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

    permission_classes = [UpdateModelPermissions]
    queryset = Patient.objects.prefetch_related(
        'hospital_patients__site',
        'relationships__type',
        'relationships__caregiver__user',
    )
    serializer_class = PatientDemographicSerializer
    pagination_class = None

    def get_object(self) -> Patient:
        """Perform a custom lookup for a `Patient` object.

        Since there is no `lookup_url` parameter in the endpoints, the lookup is performed by using the provided `mrns`.

        Returns:
            `Patient` object

        Raises:
            NotFound: if `Patient` record has not be found through the provided `mrns` list of `HospitalPatients`
        """
        # Validate the `MRNs` from input
        hospital_patient_serializer = HospitalPatientSerializer(
            data=self.request.data.get('mrns', []),
            many=True,
            allow_empty=False,
        )
        # TODO: custom error message: {'mrns': 'This list may not be empty.'}
        hospital_patient_serializer.is_valid(raise_exception=True)

        try:
            patient = self.queryset.get_patient_by_site_mrn_list(
                hospital_patient_serializer.validated_data,
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            # Raise `NotFound` if `Patient` object is empty
            raise NotFound(
                '{0} {1}'.format(
                    'Cannot find patient record with the provided MRNs and sites.',
                    'Make sure that MRN/site pairs refer to the same patient.',
                ),
            )

        # May raise a permission denied
        self.check_object_permissions(self.request, patient)

        return patient


class PatientCaregiverDevicesView(RetrieveAPIView):
    """Class handling GET requests for patient caregivers."""

    queryset = (
        Patient.objects.prefetch_related(
            'relationships__caregiver__user',
            'relationships__caregiver__devices',
        )
    )
    serializer_class = caregiver_serializers.PatientCaregiverDevicesSerializer

    lookup_url_kwarg = 'legacy_id'
    lookup_field = 'legacy_id'


class PatientUpdateView(UpdateAPIView):
    """Class handling PUT requests for patient access level update."""

    permission_classes = [CustomDjangoModelPermissions]
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_url_kwarg = 'legacy_id'
    lookup_field = 'legacy_id'

    def get_serializer(self, *args: Any, **kwargs: Any) -> Any:
        """Return the serializer instance that should be used for validating.

        And deserializing input, and for serializing output.

        Args:
            args: varied amount of non-keyword arguments
            kwargs: varied amount of keyword arguments

        Returns:
            BaseSerializer
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        kwargs['fields'] = ['data_access']
        return serializer_class(*args, **kwargs)


class PatientExistsView(APIView):
    """Class to return the Patient uuid & legacy_id given an input list of mrns and site codes.

    `get_patient_by_site_mrn_list` constructs a bitwise OR query comprised of each mrn+site pair for an efficient query.

    For example, for an input Mrn+Site list
    [
    {"site_code": "RVH", "mrn": "9999996"},
    {"site_code": "LAC", "mrn": "0765324"}
    ]

    We want to query the database using the condition:

    ```
    WHERE
    (site__location.code = 'RVH' AND hospital_patient.mrn = '9999996')
    OR
    (site__location.code = 'LAC' AND hospital_patient.mrn = '0765324')
    AND hospital_patient.is_active = True;
    ```
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Handle POST requests from `patients/exists`.

        Args:
            request: List of mrn & site dictionary objects

        Raises:
            NotFound: if `Patient` record has not been found through the provided `mrns` list of `HospitalPatients`

        Returns:
            uuid & legacy_id for the `Patient` object
        """
        # Make `is_active` not required for cases when OIE calling the API without knowing if Patient is active in Opal
        serializer = HospitalPatientSerializer(
            fields=('mrn', 'site_code'),
            data=request.data,
            many=True,
        )

        if serializer.is_valid():
            mrn_site_data = serializer.validated_data

            try:
                patient = Patient.objects.get_patient_by_site_mrn_list(mrn_site_data)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                raise NotFound(
                    detail='{0} {1}'.format(
                        'Cannot find patient record with the provided MRNs and sites or',
                        'multiple patients found.',
                    ),
                )
            return Response(
                data=PatientSerializer(patient, fields=('uuid', 'legacy_id')).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
