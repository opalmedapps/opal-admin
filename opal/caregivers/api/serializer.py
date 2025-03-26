"""This module provides Django REST framework serializers for GetRegistrationEncryptionInfoView api return value."""
from rest_framework import serializers

from opal.caregivers.models import RegistrationCode
from opal.patients.serializer import HospitalPatientRegistrationSerializer, PatientRegistrationSerializer


class RegistrationEncryptionInfoSerializer(serializers.ModelSerializer):
    """Serializer for the return value of registration encrytion info."""

    patient = PatientRegistrationSerializer(source='relationship.patient', many=False, read_only=True)
    hospital_patients = HospitalPatientRegistrationSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['code', 'status', 'patient', 'hospital_patients']
