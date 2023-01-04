"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.db.models import Q as Q_Object
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from opal.caregivers.api.serializers import RegistrationCodePatientDetailedSerializer, RegistrationCodePatientSerializer
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus
from opal.core.drf_permissions import CaregiverPatientPermissions, CustomPatientDemographicPermissions
from opal.patients.api.serializers import CaregiverRelationshipSerializer, PatientDemographicSerializer
from opal.patients.models import HospitalPatient, Patient, Relationship


class RetrieveRegistrationDetailsView(RetrieveAPIView):
    """Class handling GET requests for registration code values."""

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).filter(
            status=RegistrationCodeStatus.NEW,
            relationship__patient__date_of_death=None,
        )
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
            return RegistrationCodePatientDetailedSerializer

        return RegistrationCodePatientSerializer


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


class PatientDemographicView(UpdateAPIView):
    """REST API `UpdateAPIView` handling PUT and PATCH requests for patient demographic updates."""

    permission_classes = [IsAuthenticated, CustomPatientDemographicPermissions]
    queryset = Patient.objects.prefetch_related('hospital_patients')
    serializer_class = PatientDemographicSerializer
    pagination_class = None

    def get_object(self) -> Any:
        """Perform a custom lookup for a `Patient` object.

        Returns:
            `Patient` object

        Raises:
            NotFound: exception
        """
        # Validate the `MRNs` from input
        serializer = PatientDemographicSerializer(
            data=self.request.data,
            fields=('mrns',),
        )
        serializer.is_valid(raise_exception=True)

        # Create flat lists of MRNs and sites
        mrns = [hosp_patient['mrn'] for hosp_patient in serializer.validated_data['hospital_patients']]
        sites = [hosp_patient['site']['code'] for hosp_patient in serializer.validated_data['hospital_patients']]

        # Get `HospitalPatient` queryset filtered by MRNs AND site codes
        hospital_patients = HospitalPatient.objects.filter(
            Q_Object(mrn__in=mrns) & Q_Object(site__code__in=sites),
        )

        # Get first `HospitalPatient` object from the queryset
        hospital_patient = hospital_patients.first()

        # Raise `NotFound` if `HospitalPatient` queryset is empty
        if not hospital_patient:
            raise NotFound({'detail': 'Cannot find patient records with the provided MRNs and site codes.'})

        # Raise `NotFound` if the `Patient` objects in the queryset are not the same (refers to different patients)
        if len(hospital_patients) != hospital_patients.filter(patient_id=hospital_patient.patient_id).count():
            raise NotFound(
                {
                    'detail': '{0} {1}'.format(
                        'Provided MRN and site code pairs belong to different patients.',
                        'MRN/site code pairs should refer to the same patient.',
                    ),
                },
            )

        return get_object_or_404(self.get_queryset(), id=hospital_patient.patient_id)
