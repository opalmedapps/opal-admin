"""This module provides Django REST framework serializers for Caregiver apis."""
from typing import Dict

from rest_framework import serializers

from opal.caregivers.models import (
    CaregiverProfile,
    Device,
    EmailVerification,
    RegistrationCode,
    SecurityAnswer,
    SecurityQuestion,
)
from opal.core.api.serializers import DynamicFieldsSerializer
from opal.hospital_settings.api.serializers import InstitutionSerializer
from opal.hospital_settings.models import Institution
from opal.patients.api.serializers import HospitalPatientSerializer, PatientSerializer
from opal.patients.models import Patient


class EmailVerificationSerializer(DynamicFieldsSerializer):
    """Serializer for model EmailVerification."""

    class Meta:
        model = EmailVerification
        fields = ['id', 'code', 'email', 'is_verified', 'sent_at']


class RegistrationEncryptionInfoSerializer(serializers.ModelSerializer):
    """Serializer for the return value of registration encryption info."""

    patient = PatientSerializer(
        source='relationship.patient',
        fields=('ramq',),
        many=False,
        read_only=True,
    )
    hospital_patients = HospitalPatientSerializer(
        source='relationship.patient.hospital_patients',
        fields=('mrn', 'is_active'),
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
        fields=('first_name', 'last_name', 'date_of_birth', 'sex', 'ramq'),
        many=False,
        read_only=True,
    )
    hospital_patients = HospitalPatientSerializer(
        source='relationship.patient.hospital_patients',
        fields=('mrn', 'site_code'),
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


class SecurityAnswerQuestionSerializer(serializers.ModelSerializer):
    """Serializer for `SecurityAnswer` questions without answers."""

    class Meta:
        model = SecurityAnswer
        fields = ['id', 'question']


class VerifySecurityAnswerSerializer(serializers.ModelSerializer):
    """Serializer for Verify security answers."""

    answer = serializers.CharField(max_length=128)  # noqa: WPS432

    class Meta:
        model = SecurityAnswer
        fields = ['answer']


class DeviceSerializer(DynamicFieldsSerializer):
    """Serializer for devices."""

    class Meta:
        model = Device
        fields = ['id', 'caregiver', 'device_id', 'type', 'is_trusted', 'push_token', 'modified']


class SecurityAnswerSerializer(DynamicFieldsSerializer):
    """Serializer for security answers with corresponding questions."""

    class Meta:
        model = SecurityAnswer
        fields = ['id', 'question', 'answer']


class CaregiverSerializer(DynamicFieldsSerializer):
    """Serializer for caregiver profile."""

    language = serializers.CharField(source='user.language')
    phone_number = serializers.CharField(source='user.phone_number')
    devices = DeviceSerializer(
        fields=('type', 'push_token'),
        many=True,
    )

    class Meta:
        model = CaregiverProfile
        fields = [
            'uuid',
            'language',
            'phone_number',
            'devices',
        ]


class RegistrationRegisterSerializer(DynamicFieldsSerializer):
    """RegistrationCode serializer used to get patient and caregiver information.

    The information include Patient and Caregiver data.
    """

    patient = PatientSerializer(
        source='relationship.patient',
        fields=('legacy_id',),
        many=False,
    )

    caregiver = CaregiverSerializer(
        source='relationship.caregiver',
        fields=('language', 'phone_number'),
        many=False,
    )
    security_answers = SecurityAnswerSerializer(
        fields=('question', 'answer'),
        many=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'caregiver', 'security_answers']


class PatientCaregiversSerializer(DynamicFieldsSerializer):
    """
    Serializer for patient and caregiver information.

    The serializer provides the name of the patient as well as the patient's caregivers and their devices.
    """

    caregivers = CaregiverSerializer(
        fields=('language', 'devices'),
        many=True,
    )

    institution_code = serializers.SerializerMethodField()

    def get_institution_code(self, obj: Patient) -> str:  # noqa: WPS615
        """
        Get a single institution code.

        Args:
            obj: Object of Patient.

        Returns:
            code of the singleton institution
        """
        return Institution.objects.get().code

    class Meta:
        model = Patient
        fields = [
            'first_name',
            'last_name',
            'institution_code',
            'caregivers',
        ]
