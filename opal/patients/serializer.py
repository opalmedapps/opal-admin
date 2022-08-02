"""Module that contains serializer classes for patient models."""
from rest_framework import serializers

from opal.patients.models import HospitalPatient, Patient, Relationship


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """Patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = Patient
        fields = ['health_insurance_number']


class HospitalPatientRegistrationSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active']


class RelationshipStatusSerializer(serializers.ModelSerializer):
    """Serializer to return patient caregive relationship status."""

    class Meta:
        model = Relationship
        fields = ['status']


class CaregiverPatientListSerializer(serializers.ModelSerializer):
    """Serializer for the list of patient for a given caregiver."""

    status = RelationshipStatusSerializer(
        source='caregivers.relationships',
        many=True,
        read_only=True,
    )

    class Meta:
        model = Patient
        fields = ['id', 'legacy_id', 'first_name', 'last_name', 'status']
