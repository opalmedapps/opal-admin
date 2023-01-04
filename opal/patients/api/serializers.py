"""This module provides Django REST framework serializers related to the `patients` app's models."""
from typing import Any, Dict, List

from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.patients.models import HospitalPatient, Patient, Relationship


class PatientSerializer(DynamicFieldsSerializer):
    """
    Patient serializer.

    The serializer, which inherits from core.api.serializers.DynamicFieldsSerializer,
    is used to get patient information according to the 'fields' arguments.
    """

    class Meta:
        model = Patient
        fields = [
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

    id = serializers.IntegerField(required=False)
    site_code = serializers.CharField(source='site.code')

    class Meta:
        model = HospitalPatient
        fields = ['id', 'site_code', 'mrn', 'is_active']

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

    mrns = PatientDemographicHospitalPatientSerializer(many=True, required=True, source='hospital_patients')

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

    def validate_mrns(
        self,
        value: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Check that `MRNs` list is not empty and there are no duplications for the `Sites`.

        At least one MRN-site pair should exist in the database.

        Args:
            value: list of the `HospitalPatients`

        Returns:
            validated `HospitalPatient` values

        Raises:
            ValidationError: if there are `Site` duplications or all the provided MRNs do not exist
        """
        if not value:
            raise serializers.ValidationError('Provided `MRNs` list is empty.')

        # Get list of site codes
        sites = [hospital_patient['site']['code'] for hospital_patient in value]

        # Compare length for unique elements
        if len(set(sites)) != len(sites):
            raise serializers.ValidationError(
                'Provided `MRNs` list contains duplicated "site" codes. Site codes should be unique.',
            )

        # Check if at least one MRN/Site pair exists. If a pair does not exist it should contain `is_active` field
        hospital_patients = HospitalPatient.objects.all()
        patient_exists = False
        for patient in value:
            if not hospital_patients.filter(site__code=patient['site']['code']).exists():
                raise serializers.ValidationError(
                    '{0}{1}{2}'.format('Provided "', patient['site']['code'], '" site code does not exist.'),
                )

            hospital_patient = hospital_patients.filter(
                mrn=patient['mrn'],
                site__code=patient['site']['code'],
            )

            if (
                not hospital_patient
                and 'is_active' not in patient
            ):
                raise serializers.ValidationError(
                    '{0} {1} {2}'.format(
                        patient['mrn'],
                        patient['site']['code'],
                        'pair does not exist. The dictionary should contain `is_active` key',
                    ),
                )

            if not patient_exists and hospital_patient:
                patient_exists = True

        if not patient_exists:
            raise serializers.ValidationError('The provided "MRNs" list should contain "MRN/site" pair that exists in the database')

        return value

    def update(self, instance, validated_data):

        # TODO: update `HospitalPatient` and `User` records
        # hospital_patients = validated_data.get('hospital_patients')

        # for item in hospital_patients:
        #     hospital_patient_id = item.get('id', None)
        #     if hospital_patient_id:
        #         hospital_patient = HospitalPatient.objects.get(id=hospital_patient_id, patient=instance)
        #         # hospital_patient.site.code = item.get('site.code', hospital_patient.site.code)
        #         hospital_patient.mrn = item.get('mrn', hospital_patient.mrn)
        #         hospital_patient.is_active = item.get('is_active', hospital_patient.is_active)
        #     else:
        #         site = Site.objects.get(code=item['site']['code'])
        #         item.pop('site')
        #         HospitalPatient.objects.create(patient=instance, site=site, **item)

        validated_data.pop('hospital_patients')
        # Runs the original parent update(), since the nested fields were 'popped' out of the data
        return super().update(instance, validated_data)
