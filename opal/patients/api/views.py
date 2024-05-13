"""This module provides `APIViews` for the `patients` app REST APIs."""
from typing import Any

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models.query import QuerySet

from rest_framework import mixins, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers import models as caregiver_models
from opal.caregivers.api import serializers as caregiver_serializers
from opal.core.drf_permissions import (
    CaregiverSelfPermissions,
    FullDjangoModelPermissions,
    IsInterfaceEngine,
    IsLegacyBackend,
    IsListener,
    IsRegistrationListener,
)

from ..api.serializers import (
    CaregiverRelationshipSerializer,
    HospitalPatientSerializer,
    PatientDemographicSerializer,
    PatientSerializer,
    PatientUpdateSerializer,
    RelationshipTypeDescriptionSerializer,
)
from ..models import Patient, Relationship, RelationshipType


class RetrieveRegistrationDetailsView(RetrieveAPIView[caregiver_models.RegistrationCode]):
    """Class handling GET requests for registration code values."""

    queryset = (
        caregiver_models.RegistrationCode.objects.select_related(
            'relationship__patient',
            'relationship__caregiver',
        ).filter(
            status=caregiver_models.RegistrationCodeStatus.NEW,
        )
    )
    serializer_class = caregiver_serializers.RegistrationCodeInfoSerializer
    permission_classes = (IsRegistrationListener,)
    lookup_url_kwarg = 'code'
    lookup_field = 'code'

    def get_object(self) -> caregiver_models.RegistrationCode:
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


class CaregiverRelationshipView(ListAPIView[Relationship]):
    """REST API `ListAPIView` returning list of caregivers for a given patient."""

    serializer_class = CaregiverRelationshipSerializer
    permission_classes = (IsListener, CaregiverSelfPermissions)

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


class PatientDemographicView(UpdateAPIView[Patient]):
    """REST API `UpdateAPIView` handling PUT and PATCH requests for patient demographic updates."""

    permission_classes = (IsInterfaceEngine,)
    queryset = Patient.objects.prefetch_related(
        'hospital_patients__site',
        'relationships__type',
        'relationships__caregiver__user',
    )
    serializer_class = PatientDemographicSerializer

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


class PatientCaregiverDevicesView(RetrieveAPIView[Patient]):
    """Class handling GET requests for patient caregivers."""

    queryset = Patient.objects.prefetch_related(
        'caregivers__user',
        'caregivers__devices',
    )
    permission_classes = (IsLegacyBackend | IsListener,)
    serializer_class = caregiver_serializers.PatientCaregiverDevicesSerializer

    lookup_url_kwarg = 'legacy_id'
    lookup_field = 'legacy_id'


class PatientView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIView[Patient]):
    """View supporting patient retrieval and (limited) update based on their legacy ID."""

    # clinical staff in OpalAdmin can update a patient (requires `change_patient`)
    # opal-labs/legacy backend retrieves patient information (requires (`view_patient`)
    permission_classes = (FullDjangoModelPermissions,)
    queryset = Patient.objects.all()
    lookup_url_kwarg = 'legacy_id'
    lookup_field = 'legacy_id'

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle a GET request to retrieve a patient instance.

        Args:
            request: the HTTP request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the HTTP response
        """
        self.serializer_class = PatientSerializer
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle a PUT request to update a patient instance.

        Args:
            request: the HTTP request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the HTTP response
        """
        self.serializer_class = PatientUpdateSerializer
        return self.update(request, *args, **kwargs)


class PatientExistsView(APIView):
    """Class to return the Patient uuid & legacy_id given an input list of mrns and site acronyms.

    `get_patient_by_site_mrn_list` constructs a bitwise OR query comprised of each mrn+site pair for an efficient query.

    For example, for an input Mrn+Site list
    [
    {"site_code": "RVH", "mrn": "9999996"},
    {"site_code": "LAC", "mrn": "0765324"}
    ]

    We want to query the database using the condition:

    ```
    WHERE
    (site__location.acronym = 'RVH' AND hospital_patient.mrn = '9999996')
    OR
    (site__location.acronym = 'LAC' AND hospital_patient.mrn = '0765324')
    AND hospital_patient.is_active = True;
    ```
    """

    permission_classes = (IsInterfaceEngine,)

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


class RelationshipTypeView(ListAPIView[RelationshipType]):
    """Rest API `ListAPIView` returning list of relationship type names and decsriptions."""

    queryset = RelationshipType.objects.all()
    permission_classes = (IsListener,)
    serializer_class = RelationshipTypeDescriptionSerializer
