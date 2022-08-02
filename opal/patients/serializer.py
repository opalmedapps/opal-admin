"""Module that contains serializer classes for patient models."""
from typing import Union

from rest_framework import serializers

from opal.patients.models import HospitalPatient, Patient


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


class CaregiverPatientListSerializer(serializers.ModelSerializer):
    """Serializer for the list of patient for a given caregiver."""

    status = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'legacy_id', 'first_name', 'last_name', 'status']

    def get_status(self, patient: Patient) -> Union[str, None]:
        """
        Get status of the relationship.

        Args:
            patient: Patient object related to the given caregiver.

        Returns:
            Status of the relationship
        """
        return patient.relationships.first().status
