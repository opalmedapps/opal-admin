"""This module provides Django REST framework serializers for GetRegistrationEncryptionInfoView api return value."""
from typing import Dict

from rest_framework import serializers

from opal.caregivers.models import RegistrationCode, SecurityAnswer, SecurityQuestion
from opal.hospital_settings.api.serializers import InstitutionSerializer
from opal.hospital_settings.models import Institution
from opal.patients.api.serializers import (
    HospitalPatientAndSiteSerializer,
    HospitalPatientRegistrationSerializer,
    PatientSerializer,
)


class RegistrationEncryptionInfoSerializer(serializers.ModelSerializer):
    """Serializer for the return value of registration encrytion info."""

    patient = PatientSerializer(
        source='relationship.patient',
        fields=('ramq',),
        many=False,
        read_only=True,
    )
    hospital_patients = HospitalPatientRegistrationSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['code', 'status', 'patient', 'hospital_patients']


class RegistrationCodePatientSerializer(serializers.ModelSerializer):
    """Serializer that is providing summary info of a patient using `RegistrationCode` model."""

    patient = PatientSerializer(
        source='relationship.patient',
        fields=('first_name', 'last_name'),
        many=False,
        read_only=True,
    )
    institution = serializers.SerializerMethodField()

    def get_institution(self, obj: RegistrationCode) -> Dict:  # noqa: WPS615
        """
        Get a single institution data.

        Args:
            obj (RegistrationCode): Object of RegistrationCode.

        Returns:
            `Institution` information where the patient is being registered at.
        """
        return InstitutionSerializer(Institution.objects.get(), fields=('id', 'name')).data

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'institution']


class RegistrationCodePatientDetailedSerializer(serializers.ModelSerializer):
    """Serializer that is providing detailed info of a patient using `RegistrationCode` model."""

    patient = PatientSerializer(
        source='relationship.patient',
        many=False,
        read_only=True,
    )
    hospital_patients = HospitalPatientAndSiteSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'hospital_patients']


class SecurityQuestionSerializer(serializers.ModelSerializer):
    """Serializer for security questions."""

    class Meta:
        model = SecurityQuestion
        fields = ['id', 'title_en', 'title_fr']


class UpdateSecurityAnswerSerializer(serializers.ModelSerializer):
    """Serializer for security answers."""

    class Meta:
        model = SecurityAnswer
        fields = ['id', 'question', 'answer']


class SecurityAnswerSerializer(serializers.ModelSerializer):
    """Serializer for security answers."""

    class Meta:
        model = SecurityAnswer
        fields = ['id', 'question']


class VerifySecurityAnswerSerializer(serializers.ModelSerializer):
    """Serializer for Verify security answers."""

    answer = serializers.CharField(max_length=128)  # noqa: WPS432

    class Meta:
        model = SecurityAnswer
        fields = ['answer']
