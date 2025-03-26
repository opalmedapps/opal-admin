"""This module provides Django REST framework serializers for Caregiver apis."""
from typing import Any

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
from opal.patients.api.serializers import HospitalPatientSerializer, PatientSerializer, RelationshipTypeSerializer
from opal.patients.models import Patient, RelationshipStatus


class EmailVerificationSerializer(DynamicFieldsSerializer[EmailVerification]):
    """Serializer for model EmailVerification."""

    class Meta:
        model = EmailVerification
        fields = ['id', 'code', 'email', 'is_verified', 'sent_at']


class RegistrationEncryptionInfoSerializer(serializers.ModelSerializer[RegistrationCode]):
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


class RegistrationCodePatientSerializer(serializers.ModelSerializer[RegistrationCode]):
    """Serializer that is providing summary info of a patient using `RegistrationCode` model."""

    patient = PatientSerializer(
        source='relationship.patient',
        fields=('first_name', 'last_name'),
        many=False,
        read_only=True,
    )
    institution = serializers.SerializerMethodField()

    def get_institution(self, obj: RegistrationCode) -> dict[str, Any]:  # noqa: WPS615
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


class SecurityQuestionSerializer(serializers.ModelSerializer[SecurityQuestion]):
    """Serializer for security questions."""

    class Meta:
        model = SecurityQuestion
        fields = ['id', 'title_en', 'title_fr']


class SecurityAnswerQuestionSerializer(serializers.ModelSerializer[SecurityAnswer]):
    """Serializer for `SecurityAnswer` questions without answers."""

    class Meta:
        model = SecurityAnswer
        fields = ['id', 'question']


class VerifySecurityAnswerSerializer(serializers.ModelSerializer[SecurityAnswer]):
    """Serializer for Verify security answers."""

    answer = serializers.CharField(max_length=128)  # noqa: WPS432

    class Meta:
        model = SecurityAnswer
        fields = ['answer']


class DeviceSerializer(DynamicFieldsSerializer[Device]):
    """Serializer for devices."""

    class Meta:
        model = Device
        fields = ['id', 'caregiver', 'device_id', 'type', 'is_trusted', 'push_token', 'modified']


# Security: this serializer includes security answer hashes, and should only be used in secure contexts
class SecurityAnswerSerializer(DynamicFieldsSerializer[SecurityAnswer]):
    """Serializer for security answers with corresponding questions."""

    class Meta:
        model = SecurityAnswer
        fields = ['id', 'question', 'answer']


class CaregiverSerializer(DynamicFieldsSerializer[CaregiverProfile]):
    """Serializer for caregiver profile."""

    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    language = serializers.CharField(source='user.language')
    phone_number = serializers.CharField(source='user.phone_number')
    username = serializers.CharField(source='user.username')
    devices = DeviceSerializer(
        fields=('type', 'push_token'),
        many=True,
    )

    class Meta:
        model = CaregiverProfile
        fields = [
            'uuid',
            'first_name',
            'last_name',
            'language',
            'phone_number',
            'username',
            'devices',
            'legacy_id',
        ]
        # enforce proper value for legacy_id
        extra_kwargs: dict[str, dict[str, Any]] = {
            'legacy_id': {
                'allow_null': False,
                'required': True,
            },
        }


class RegistrationCodePatientDetailedSerializer(serializers.ModelSerializer[RegistrationCode]):
    """Serializer that is providing detailed info of a patient using `RegistrationCode` model."""

    caregiver = CaregiverSerializer(
        source='relationship.caregiver',
        fields=('uuid', 'first_name', 'last_name', 'legacy_id'),
        many=False,
        read_only=True,
    )
    patient = PatientSerializer(
        source='relationship.patient',
        fields=('uuid', 'first_name', 'last_name', 'date_of_birth', 'sex', 'ramq', 'legacy_id'),
        many=False,
        read_only=True,
    )
    hospital_patients = HospitalPatientSerializer(
        source='relationship.patient.hospital_patients',
        fields=('mrn', 'site_code'),
        many=True,
        read_only=True,
    )
    relationship_type = RelationshipTypeSerializer(
        source='relationship.type',
        fields=('name', 'role_type'),
        many=False,
    )

    class Meta:
        model = RegistrationCode
        fields = ['caregiver', 'patient', 'hospital_patients', 'relationship_type']


class _NestedCaregiverSerializer(CaregiverSerializer):
    """
    Caregiver profile serializer that supports nested updates.

    The unique validator on legacy_id otherwise fails when the legacy_id already exists.

    See: https://github.com/encode/django-rest-framework/issues/2996
    See: https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
    """

    class Meta(CaregiverSerializer.Meta):
        extra_kwargs = {
            'legacy_id': dict(CaregiverSerializer.Meta.extra_kwargs['legacy_id'], validators=[]),
        }


class _NestedPatientSerializer(PatientSerializer):
    """
    Patient serializer that supports nested updates.

    The unique validator on legacy_id otherwise fails when the legacy_id already exists.

    See: https://github.com/encode/django-rest-framework/issues/2996
    See: https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
    """

    class Meta(PatientSerializer.Meta):
        extra_kwargs = {
            # enforce proper value for legacy_id
            'legacy_id': {
                'allow_null': False,
                'required': True,
                'validators': [],
            },
        }


class RegistrationRegisterSerializer(DynamicFieldsSerializer[RegistrationCode]):
    """RegistrationCode serializer used to get patient and caregiver information.

    The information include Patient and Caregiver data.
    """

    patient = _NestedPatientSerializer(
        source='relationship.patient',
        fields=('legacy_id',),
        many=False,
    )

    caregiver = _NestedCaregiverSerializer(
        source='relationship.caregiver',
        fields=('language', 'phone_number', 'username', 'legacy_id'),
        many=False,
    )
    security_answers = SecurityAnswerSerializer(
        fields=('question', 'answer'),
        many=True,
        required=False,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'caregiver', 'security_answers']


class PatientCaregiverDevicesSerializer(DynamicFieldsSerializer[Patient]):
    """
    Serializer for patient and caregiver information.

    The serializer provides the name of the patient as well as the patient's caregivers and their devices.
    """

    caregivers = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()

    def get_institution(self, obj: Patient) -> dict[str, str]:  # noqa: WPS615
        """
        Get a single institution acronym.

        Args:
            obj: Object of Patient.

        Returns:
            acronym of the singleton institution
        """
        return Institution.objects.values('acronym_en', 'acronym_fr').get()

    def get_caregivers(self, obj: Patient) -> dict[str, Any]:  # noqa: WPS615
        """
        Return the active caregivers of the patient.

        A caregiver is active if it has a confirmed relationship with the patient.

        Args:
            obj: the patient

        Returns:
            the caregivers of the patient with confirmed relationships
        """
        caregivers = obj.caregivers.filter(relationships__status=RelationshipStatus.CONFIRMED)
        return CaregiverSerializer(
            caregivers,
            fields=('language', 'username', 'devices'),
            many=True,
        ).data

    class Meta:
        model = Patient
        fields = [
            'first_name',
            'last_name',
            'data_access',
            'institution',
            'caregivers',
        ]
