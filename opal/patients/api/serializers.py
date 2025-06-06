# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides Django REST framework serializers related to the `patients` app's models."""

from typing import Any

from django.db import transaction

from rest_framework import serializers
from rest_framework.fields import empty

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.hospital_settings.models import Site
from opal.patients.models import HospitalPatient, Patient, Relationship, RelationshipType, RoleType


class PatientSerializer(DynamicFieldsSerializer[Patient]):
    """
    Patient serializer.

    The serializer, which inherits from core.api.serializers.DynamicFieldsSerializer,
    is used to get patient information according to the 'fields' arguments.
    """

    class Meta:
        model = Patient
        fields = [
            'uuid',
            'legacy_id',
            'first_name',
            'last_name',
            'date_of_birth',
            'date_of_death',
            'data_access',
            'sex',
            'ramq',
            'is_adult',
            'non_interpretable_lab_result_delay',
            'interpretable_lab_result_delay',
        ]


class PatientUpdateSerializer(serializers.ModelSerializer[Patient]):
    """Patient serializer to update a patient instance."""

    class Meta:
        model = Patient
        fields = [
            'data_access',
        ]
        extra_kwargs: dict[str, dict[str, Any]] = {
            'data_access': {
                'required': True,
                # remove empty since the field is required
                'default': empty,
            },
        }


class PatientUUIDSerializer(serializers.Serializer[Patient]):
    """Serializer for patient's UUID."""

    patient_uuid = serializers.UUIDField(required=True, allow_null=False)


class HospitalPatientSerializer(DynamicFieldsSerializer[HospitalPatient]):
    """
    Serializer for converting and validating `HospitalPatient` objects/data.

    The serializer inherits from `core.api.serializers.DynamicFieldsSerializer`,
    and also provides `HospitalPatient` info and the site acronym according to the 'fields' arguments.
    """

    site_code = serializers.CharField(source='site.acronym')

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active', 'site_code']
        # make the is_active field required
        # need to remove the derault in order to avoid the "May not set both `required` and `default" assertion error
        extra_kwargs = {'is_active': {'required': True, 'default': empty}}

    def validate_site_code(self, value: str) -> str:
        """
        Check that `site_code` exists in the database (e.g., RVH).

        Args:
            value: site acronym to be validated

        Returns:
            validated site acronym value

        Raises:
            ValidationError: if provided site acronym does not exist in the database
        """
        if not Site.objects.filter(acronym=value).exists():
            raise serializers.ValidationError(f'Provided "{value}" site acronym does not exist.')
        return value


class RelationshipTypeSerializer(DynamicFieldsSerializer[RelationshipType]):
    """Serializer for the RelationshipType model."""

    class Meta:
        model = RelationshipType
        fields = [
            'id',
            'name',
            'description',
            'start_age',
            'end_age',
            'form_required',
            'can_answer_questionnaire',
            'role_type',
        ]


class RelationshipTypeDescriptionSerializer(RelationshipTypeSerializer):
    """Serializer for the list of names and descriptions of the RelationshipType model."""

    class Meta:
        model = RelationshipType
        fields = [
            'name',
            'description',
        ]


class CaregiverPatientSerializer(serializers.ModelSerializer[Relationship]):
    """Serializer for the list of patients for a given caregiver."""

    patient_uuid = serializers.UUIDField(source='patient.uuid')
    patient_legacy_id = serializers.IntegerField(source='patient.legacy_id')
    first_name = serializers.CharField(source='patient.first_name')
    last_name = serializers.CharField(source='patient.last_name')
    relationship_type = RelationshipTypeSerializer(
        source='type',
        fields=('id', 'name', 'can_answer_questionnaire', 'role_type'),
        many=False,
    )
    relationship_type_name = serializers.CharField(source='type.name')
    data_access = serializers.CharField(source='patient.data_access')
    non_interpretable_lab_result_delay = serializers.IntegerField(source='patient.non_interpretable_lab_result_delay')
    interpretable_lab_result_delay = serializers.IntegerField(source='patient.interpretable_lab_result_delay')

    class Meta:
        model = Relationship
        fields = [
            'patient_uuid',
            'patient_legacy_id',
            'first_name',
            'last_name',
            'status',
            'relationship_type',
            'relationship_type_name',
            'data_access',
            'non_interpretable_lab_result_delay',
            'interpretable_lab_result_delay',
        ]


class CaregiverRelationshipSerializer(serializers.ModelSerializer[Relationship]):
    """Serializer for the list of caregivers for a given patient."""

    caregiver_id = serializers.IntegerField(source='caregiver.user.id')
    first_name = serializers.CharField(source='caregiver.user.first_name')
    last_name = serializers.CharField(source='caregiver.user.last_name')
    relationship_type = serializers.CharField(source='type.name')

    class Meta:
        model = Relationship
        fields = ['caregiver_id', 'first_name', 'last_name', 'status', 'relationship_type']


class PatientDemographicSerializer(DynamicFieldsSerializer[Patient]):
    """Serializer for patient's personal info received from the `patient demographic update` endpoint."""

    mrns = HospitalPatientSerializer(many=True, allow_empty=False, required=True)

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
        ]

    @transaction.atomic
    def update(
        self,
        instance: Patient,
        validated_data: dict[str, Any],
    ) -> Patient:
        """
        Update `Patient` instance during patient demographic update call.

        It updates `User` fields as well.

        Args:
            instance: `Patient` record to be updated
            validated_data: dictionary containing validated request data

        Returns:
            updated `Patient` record
        """
        # Update the fields of the `Patient` instance
        super().update(instance, validated_data)

        # Update the `HospitalPatient` records with the new demographic information
        for hospital_patient in validated_data.get('mrns', []):
            # Update or create hospital patient instances based on a patient & MRN & site lookup
            # Update the is_active field
            # See details on update_or_create:
            # https://docs.djangoproject.com/en/dev/ref/models/querysets/#django.db.models.query.QuerySet.update_or_create
            HospitalPatient.objects.update_or_create(
                mrn=hospital_patient['mrn'],
                site=Site.objects.filter(acronym=hospital_patient['site']['acronym']).first(),
                patient=instance,
                defaults={
                    'is_active': hospital_patient['is_active'],
                },
            )

        # Update the `User` model with the new demographic information.
        # If a patient does not have a self relationship it means there is no user for this patient.
        # In that case the user-related fields would not be updated.

        # Look up the `Relationships` to the updating patient with a `SELF` role type
        relationship = instance.relationships.filter(
            type__role_type=RoleType.SELF,
        ).first()

        if relationship:
            user = relationship.caregiver.user
            user.first_name = validated_data.get(
                'first_name',
                relationship.caregiver.user.first_name,
            )
            user.last_name = validated_data.get(
                'last_name',
                relationship.caregiver.user.last_name,
            )
            user.save()

        return instance
