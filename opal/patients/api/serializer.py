"""This module provides Django REST framework serializers for PatietnView api return value."""
from typing import Any
from rest_framework import serializers

from opal.caregivers.models import RegistrationCode
from opal.patients.serializer import (
    HospitalInstitutionSerializer,
    PatientDetailSerializer,
    PatientRegistrationSerializer,
)


class RegistrationCodePatientSerializer(serializers.ModelSerializer):
    """Serializer for the return value of registration code."""
    patient = PatientRegistrationSerializer(source='relationship.patient', many=False, read_only=True)
    institutions = HospitalInstitutionSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'institutions']


class RegistrationCodePatientDetailedSerializer(serializers.ModelSerializer):
    """Serializer for the return value of registration code."""
    patient = PatientDetailSerializer(source='relationship.patient', many=False, read_only=True)
    institutions = HospitalInstitutionSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'institutions']
