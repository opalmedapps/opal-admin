"""This module provides Django REST framework serializers related to the `patients` app's models."""
from typing import Any, Dict, List, Optional

from django.db import transaction

from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.hospital_settings.models import Site
from opal.patients.models import HospitalPatient, Patient, Relationship, RelationshipType


class PatientSerializer(DynamicFieldsSerializer):
    """
    Patient serializer.

    The serializer, which inherits from core.api.serializers.DynamicFieldsSerializer,
    is used to get patient information according to the 'fields' arguments.
    """

    # legacy_id default is null, to verify it with serializer properly,
    # add a special field here for it.
    legacy_id = serializers.IntegerField(min_value=1)  # noqa: WPS432

    class Meta:
        model = Patient
        fields = [
            'legacy_id',
            'first_name',
            'last_name',
            'date_of_birth',
            'date_of_death',
            'sex',
            'ramq',
        ]


class HospitalPatientSerializer(DynamicFieldsSerializer):
    """
    Hospital patient serializer.

    The serializer inherits from core.api.serializers.DynamicFieldsSerializer,
    and also provides HospitalPatient info and the site code according to the 'fields' arguments.
    """

    site_code = serializers.CharField(
        source='site.code',
        read_only=True,
    )

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active', 'site_code']


class CaregiverPatientSerializer(serializers.ModelSerializer):
    """Serializer for the list of patients for a given caregiver."""

    patient_id = serializers.IntegerField(source='patient.id')
    patient_legacy_id = serializers.IntegerField(source='patient.legacy_id')
    first_name = serializers.CharField(source='patient.first_name')
    last_name = serializers.CharField(source='patient.last_name')

    class Meta:
        model = Relationship
        fields = ['patient_id', 'patient_legacy_id', 'first_name', 'last_name', 'status']


class CaregiverRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for the list of caregivers for a given patient."""

    caregiver_id = serializers.IntegerField(source='caregiver.user.id')
    first_name = serializers.CharField(source='caregiver.user.first_name')
    last_name = serializers.CharField(source='caregiver.user.last_name')

    class Meta:
        model = Relationship
        fields = ['caregiver_id', 'first_name', 'last_name', 'status']


class PatientDemographicHospitalPatientSerializer(serializers.ModelSerializer):
    """Serializer for converting and validating `MRNs` received from the `patient demographic update` endpoint."""

    site_code = serializers.CharField(source='site.code')

    class Meta:
        model = HospitalPatient
        fields = ['site_code', 'mrn', 'is_active']

    def validate_site_code(self, value: str) -> str:
        """Check that `site_code` exists in the database (e.g., MGH).

        Args:
            value: site code to be validated

        Returns:
            validated site code value

        Raises:
            ValidationError: if provided site code does not exist in the database
        """
        if not HospitalPatient.objects.filter(site__code=value).exists():
            raise serializers.ValidationError(
                '{0}{1}{2}'.format('Provided "', value, '" site code does not exist.'),
            )
        return value


class PatientDemographicSerializer(DynamicFieldsSerializer):
    """Serializer for patient's personal info received from the `patient demographic update` endpoint."""

    mrns = PatientDemographicHospitalPatientSerializer(many=True, required=True)

    class Meta:
        model = Patient
        fields = [
            'ramq',
            'first_name',
            'last_name',
            'date_of_birth',
            'date_of_death',
            'sex',
            'mrns',
            # TODO:
            # 'phone',
            # 'email',
            # 'language',
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the serializer for patient demographic operations.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.hospital_patient_queryset = HospitalPatient.objects.all()

    def validate_mrns(
        self,
        value: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Check that `MRNs` list is not empty and there are no duplications for the `Sites`.

        At least one MRN/site code pair should exist in the database.

        If MRN/site code pair is new, it should contain `is_active` key.

        Args:
            value: list of the `HospitalPatients`

        Returns:
            validated `HospitalPatient` values

        Raises:
            ValidationError: if there are `Site` duplications or all the provided MRNs do not exist
        """
        if not value:
            raise serializers.ValidationError('Provided `MRNs` list is empty.')

        self._check_site_codes_uniqueness(value)

        # Check if at least one MRN/Site pair exists. If a pair does not exist it should contain `is_active` field
        self._check_mrn_site_pair_exists(value)

        return value

    @transaction.atomic
    def update(
        self,
        instance: Patient,
        validated_data: Dict[str, Any],
    ) -> Optional[Patient]:
        """Update `Patient` instance during patient demographic update call.

        Args:
            instance: `Patient` record to be updated
            validated_data: dictionary containing validated request data

        Returns:
            Optional[Patient]: updated `Patient` record
        """
        # Runs the original parent update()
        super().update(instance, validated_data)

        self._bulk_update(instance, validated_data)

        return instance

    def _check_site_codes_uniqueness(
        self,
        hospital_patients: List[Dict[str, Any]],
    ) -> None:
        """Ensure that a patient does not have more than one record at the same site.

        E.g., a patient should not have two MRN records at the same site.

        Args:
            hospital_patients: list of dictionaries that contain `HospitalPatient` records

        Raises:
            ValidationError: occurs when hospital_patients list contains duplicated "site" codes
        """
        # Get list of site codes
        sites = [hospital_patient['site']['code'] for hospital_patient in hospital_patients]

        # Compare length for unique site code elements
        if len(set(sites)) != len(sites):
            raise serializers.ValidationError(
                'Provided `MRNs` list contains duplicated "site" codes. Site codes should be unique.',
            )

    def _check_mrn_site_pair_exists(
        self,
        validated_hospital_patients: List[Dict[str, Any]],
    ) -> None:
        """Check if at least one MRN/Site pair exists.

        If a pair does not exist in the database, it should contain `is_active` field.

        Args:
            validated_hospital_patients: list of dictionaries that contain `HospitalPatient` records

        Raises:
            ValidationError: occurs when MRN/site code pair is missing `is_active` key
            ValidationError: occurs when MRN/site code pair has not been found
        """
        hospital_patients = self.hospital_patient_queryset

        for patient in validated_hospital_patients:
            hospital_patient = hospital_patients.filter(
                mrn=patient['mrn'],
                site__code=patient['site']['code'],
            )

            if (
                not hospital_patient
                and 'is_active' not in patient
            ):
                raise serializers.ValidationError(
                    '{0}/{1}: {2}'.format(
                        patient['mrn'],
                        patient['site']['code'],
                        'MRN/site code pair should contain `is_active` key if it does not exist in the database',
                    ),
                )
            else:
                hospital_patient_record = hospital_patient

        if not hospital_patient_record:
            raise serializers.ValidationError(
                'The provided "MRNs" list should contain "MRN/site" pair that exists in the database',
            )

    # TODO: refactor the following method
    def _bulk_update(  # noqa: WPS210
        self,
        patient_instance: Patient,
        validated_data: Dict[str, Any],
    ) -> None:

        hospital_patients = validated_data.get('mrns', [])

        # Update the `HospitalPatient` records with the new demographic information
        for item in hospital_patients:
            site_code = item.get('site').get('code')
            hospital_patient = self.hospital_patient_queryset.filter(
                mrn=item.get('mrn'),
                site__code=site_code,
                patient=patient_instance,
            ).first()

            if hospital_patient:
                hospital_patient.is_active = item.get('is_active', hospital_patient.is_active)
                hospital_patient.save()
            else:
                site = Site.objects.get(code=site_code)
                self.hospital_patient_queryset.create(
                    patient=patient_instance,
                    site=site,
                    mrn=item.get('mrn'),
                    is_active=item.get('is_active'),
                )

        # Update the `User` model with the new demographic information
        # TODO: use constant to find `Self` relationship
        relationship_type = RelationshipType.objects.filter(name='Self').first()
        # Look up the `Relationships` to that patient with a `Self` relationship
        relationship = Relationship.objects.filter(
            patient=patient_instance,
            type=relationship_type,
        ).first()

        if relationship:
            relationship.caregiver.user.first_name = validated_data.get(
                'first_name',
                relationship.caregiver.user.first_name,
            )
            relationship.caregiver.user.last_name = validated_data.get(
                'last_name',
                relationship.caregiver.user.last_name,
            )
            relationship.caregiver.user.save()
