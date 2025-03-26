"""This module provides Django REST framework serializers for GetRegistrationEncryptionInfoView api return value."""
from rest_framework import serializers

from opal.caregivers.models import RegistrationCode, SecurityAnswer, SecurityQuestion
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


class SecurityQuestionSerializer(serializers.ModelSerializer):
    """This class defines how a `SecurityQuestion` is serialized for an API."""

    class Meta:
        model = SecurityQuestion
        fields = ['id', 'title', 'title_en', 'title_fr', 'is_active']


class SecurityAnswerSerializer(serializers.ModelSerializer):
    """This class defines how a `SecurityAnswer` is serialized for an API."""

    class Meta:
        model = SecurityAnswer
        fields = ['id', 'user_id', 'question', 'answer']
