"""Module that contains serializer classes for patient models."""
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
