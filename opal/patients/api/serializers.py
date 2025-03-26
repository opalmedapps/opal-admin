"""This module provides Django REST framework serializers related to the `patients` app's models."""
from typing import Any, Dict, Optional

from django.db import transaction
from django.db.models import Q  # noqa: WPS347
from django.utils.translation import gettext

from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.hospital_settings.models import Site
from opal.patients.models import HospitalPatient, Patient, Relationship, RelationshipStatus, RelationshipType, RoleType


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
            'uuid',
        ]


class HospitalPatientSerializer(DynamicFieldsSerializer):
    """
    Serializer for converting and validating `HospitalPatient` objects/data.

    The serializer inherits from `core.api.serializers.DynamicFieldsSerializer`,
    and also provides `HospitalPatient` info and the site code according to the 'fields' arguments.
    """

    site_code = serializers.CharField(source='site.code')
    # make the is_active field required
    is_active = serializers.BooleanField(required=True)

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active', 'site_code']

    def validate_site_code(self, value: str) -> str:
        """Check that `site_code` exists in the database (e.g., RVH).

        Args:
            value: site code to be validated

        Returns:
            validated site code value

        Raises:
            ValidationError: if provided site code does not exist in the database
        """
        if not Site.objects.filter(code=value).exists():
            raise serializers.ValidationError(
                '{0}{1}{2}'.format('Provided "', value, '" site code does not exist.'),
            )
        return value


class RelationshipTypeSerializer(DynamicFieldsSerializer):
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


class CaregiverPatientSerializer(serializers.ModelSerializer):
    """Serializer for the list of patients for a given caregiver."""

    patient_id = serializers.IntegerField(source='patient.id')
    patient_legacy_id = serializers.IntegerField(source='patient.legacy_id')
    first_name = serializers.CharField(source='patient.first_name')
    last_name = serializers.CharField(source='patient.last_name')
    relationship_type = RelationshipTypeSerializer(
        source='type',
        fields=('id', 'name', 'can_answer_questionnaire', 'role_type'),
        many=False,
    )

    class Meta:
        model = Relationship
        fields = ['patient_id', 'patient_legacy_id', 'first_name', 'last_name', 'status', 'relationship_type']


class CaregiverRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for the list of caregivers for a given patient."""

    caregiver_id = serializers.IntegerField(source='caregiver.user.id')
    first_name = serializers.CharField(source='caregiver.user.first_name')
    last_name = serializers.CharField(source='caregiver.user.last_name')

    class Meta:
        model = Relationship
        fields = ['caregiver_id', 'first_name', 'last_name', 'status']


class PatientDemographicSerializer(DynamicFieldsSerializer):
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
        validated_data: Dict[str, Any],
    ) -> Optional[Patient]:
        """Update `Patient` instance during patient demographic update call.

        It updates `User` fields as well.

        Args:
            instance: `Patient` record to be updated
            validated_data: dictionary containing validated request data

        Returns:
            Optional[Patient]: updated `Patient` record
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
                site=Site.objects.filter(code=hospital_patient['site']['code']).first(),
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

        # Prevent caregiver and self access to the deceased patient's data by setting relationship status to expired
        if instance.date_of_death:
            self._inactivate_patient_relationships(
                patient=instance,
            )

        return instance

    def _inactivate_patient_relationships(
        self,
        patient: Patient,
    ) -> None:
        """Inactivate all the relationships for a deceased patient.

        Args:
            patient: the deceased patient object
        """
        # Look up the `Relationships` to the updating patient with a `SELF` role type
        self_relationship = patient.relationships.filter(
            type__role_type=RoleType.SELF,
        ).first()

        # Find patient's caregiver profile's ID (if patient was taking care of other patients including themselves)
        patient_caregiver_id = self_relationship.caregiver.id if self_relationship else None

        # Set end_date, reason, and status for the deceased patient's relationships
        # The updating relationships should contain records for the patient OR the patient's caregiver profile
        Relationship.objects.filter(
            Q(patient__id=patient.id) | Q(caregiver__id=patient_caregiver_id),
        ).update(
            end_date=patient.date_of_death,
            reason=gettext('Opal Account Inactivated'),
            status=RelationshipStatus.EXPIRED,
        )

        # Add the "Date of death submitted from ADT" relationship termination reason only for the `SELF` role
        Relationship.objects.filter(
            Q(patient__id=patient.id) | Q(caregiver__id=patient_caregiver_id),
            type__role_type=RoleType.SELF,
        ).update(
            reason=gettext('Date of death submitted from ADT'),
        )
