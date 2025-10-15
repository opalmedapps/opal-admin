# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides `APIViews` for the `patients` app REST APIs."""

import base64
import json
from io import BytesIO
from typing import Any

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string

import structlog
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
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
from opal.services.fhir.utils import FHIRDataRetrievalError, jwe_sh_link_encrypt, retrieve_patient_summary

from ..api.serializers import (
    CaregiverRelationshipSerializer,
    HospitalPatientSerializer,
    PatientDemographicSerializer,
    PatientSerializer,
    PatientUpdateSerializer,
    RelationshipTypeDescriptionSerializer,
)
from ..models import Patient, Relationship, RelationshipType

LOGGER = structlog.get_logger()


class RetrieveRegistrationDetailsView(RetrieveAPIView[caregiver_models.RegistrationCode]):
    """Class handling GET requests for registration code values."""

    queryset = caregiver_models.RegistrationCode.objects.select_related(
        'relationship__patient',
        'relationship__caregiver',
        'relationship__type',
    ).filter(
        status=caregiver_models.RegistrationCodeStatus.NEW,
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


@extend_schema(
    responses={
        200: CaregiverRelationshipSerializer(many=True),
        403: {'description': 'User not authorized'},
        404: {'description': 'Patient not found'},
    },
)
class CaregiverRelationshipView(ListAPIView[Relationship]):
    """REST API `ListAPIView` returning list of caregivers for a given patient."""

    serializer_class = CaregiverRelationshipSerializer
    permission_classes = (IsListener, CaregiverSelfPermissions)
    queryset = Relationship.objects.select_related('caregiver__user')

    def get_queryset(self) -> QuerySet[Relationship]:
        """
        Query set to retrieve list of caregivers for the input patient.

        Returns:
            List of caregiver profiles for a given patient
        """
        return self.queryset.filter(
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
        """
        Perform a custom lookup for a `Patient` object.

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
        except (ObjectDoesNotExist, MultipleObjectsReturned) as error:
            # Raise `NotFound` if `Patient` object is empty
            raise NotFound(
                'Cannot find patient record with the provided MRNs and sites.'
                + 'Make sure that MRN/site pairs refer to the same patient.',
            ) from error

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

    @extend_schema(
        responses={
            200: PatientSerializer,
            403: {'description': 'User not authorized'},
            404: {'description': 'Patient not found'},
        },
    )
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

    @extend_schema(
        request=PatientUpdateSerializer,
        responses={
            200: PatientUpdateSerializer,
            400: {'description': 'Bad request'},
            403: {'description': 'User not authorized'},
            404: {'description': 'Patient not found'},
        },
    )
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


@extend_schema(
    request={
        'serializer': HospitalPatientSerializer(many=True),
    },
    responses={
        200: PatientSerializer,
    },
)
class PatientExistsView(APIView):
    """
    Class to return the Patient uuid & legacy_id given an input list of mrns and site acronyms.

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
        # Make `is_active` not required for cases when source system calling
        # the API without knowing if Patient is active in Opal
        serializer = HospitalPatientSerializer(
            fields=('mrn', 'site_code'),
            data=request.data,
            many=True,
        )

        if serializer.is_valid():
            mrn_site_data = serializer.validated_data

            try:
                patient = Patient.objects.get_patient_by_site_mrn_list(mrn_site_data)
            except (ObjectDoesNotExist, MultipleObjectsReturned) as error:
                raise NotFound(
                    detail='Cannot find patient record with the provided MRNs and sites or multiple patients found.',
                ) from error
            return Response(
                data=PatientSerializer(patient, fields=('uuid', 'legacy_id')).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RelationshipTypeView(ListAPIView[RelationshipType]):
    """Rest API `ListAPIView` returning list of relationship type names and descriptions."""

    queryset = RelationshipType.objects.all()
    permission_classes = (IsListener,)
    serializer_class = RelationshipTypeDescriptionSerializer


class PatientSummaryView(APIView):
    """View to process a request to retrieve the International Patient Summary (IPS) for a given patient."""

    permission_classes = (IsListener,)

    def get(self, request: Request, uuid: str) -> Response:
        """
        Handle a GET request to retrieve the International Patient Summary (IPS) for the given patient UUID.

        Assemble the data needed to build a Smart Health Link that can be read by an IPS viewer.
        The IPS data is encrypted and stored using the configured storage backend.

        Args:
            request: HTTP request
            uuid: the patient's UUID for whom IPS link data is being generated

        Raises:
            ValidationError: if the patient has no health identification number

        Returns:
            HTTP response with the SH link payload that can be parsed by IPS viewers
        """
        patient = get_object_or_404(Patient, uuid=uuid)

        if not patient.ramq:
            raise ValidationError('Patient has no health identification number')

        # Request and assemble IPS data into a bundle
        try:
            ips, ips_uuid = retrieve_patient_summary(
                settings.FHIR_API_OAUTH_URL,
                settings.FHIR_API_URL,
                settings.FHIR_API_CLIENT_ID,
                settings.FHIR_API_PRIVATE_KEY,
                patient.ramq,
            )
        except FHIRDataRetrievalError as exc:
            LOGGER.exception('Error retrieving IPS data from FHIR server for patient %s', uuid)
            raise ValidationError('Error retrieving IPS data from FHIR server') from exc
        else:
            # Generate an encryption key for the bundle, and encrypt it
            encryption_key, encrypted_ips = jwe_sh_link_encrypt(ips)

            storage_backend_class: type = import_string(settings.IPS_STORAGE_BACKEND)
            storage_backend = storage_backend_class()
            file_name = f'{ips_uuid}.ips'

            LOGGER.debug(
                'Saving IPS bundle for patient %s to %s using storage backend %s',
                uuid,
                file_name,
                settings.IPS_STORAGE_BACKEND,
            )

            try:
                actual_file_name = storage_backend.save(file_name, BytesIO(encrypted_ips))
            # storage backends can raise various exceptions, try to catch them all
            except Exception as exc:
                LOGGER.exception(
                    'Error saving IPS bundle for patient %s to %s using storage backend %s',
                    uuid,
                    file_name,
                    settings.IPS_STORAGE_BACKEND,
                )
                raise ValidationError('Error saving IPS bundle to storage backend') from exc
            else:
                LOGGER.debug('Successfully saved IPS bundle for patient %s to %s', uuid, actual_file_name)

                # See: https://docs.smarthealthit.org/smart-health-links/spec/#construct-a-shlink-payload
                link_content = {
                    'url': f'{settings.IPS_PUBLIC_BASE_URL}/{ips_uuid}',
                    'flag': 'L',
                    'key': encryption_key,
                    'label': 'Opal-App IPS Demo',
                }

                LOGGER.debug('Constructed SH link content for patient %s', uuid, extra=link_content)

                # Convert the link content into JSON, parse it as base64, and build the SH link payload
                link_json = json.dumps(link_content)
                link_base64 = base64.b64encode(link_json.encode('utf-8')).decode('utf-8')

                return Response({'payload': link_base64})
