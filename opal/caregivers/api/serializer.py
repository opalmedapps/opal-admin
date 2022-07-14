"""This module provides Django REST framework serializers for GetRegistrationEncryptionInfo api view return value."""
from rest_framework import serializers

from opal.caregivers.models import RegistrationCode
from opal.patients.models import HospitalPatient, Patient


class PatientSerializer(serializers.ModelSerializer):
    """Patient serializer for registration."""

    class Meta:
        model = Patient
        fields = ['id']


class HospitalPatientSerializer(serializers.ModelSerializer):
    """Hostipal patient serializer for registration."""

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active']


class RegistrationEncryptionInfoSerializer(serializers.ModelSerializer):
    """Serializer for the return value of registration encrytion info."""

    patient = PatientSerializer(source='relationship.patient', many=False, read_only=True)
    hospital_patients = HospitalPatientSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['code', 'status', 'patient', 'hospital_patients']
