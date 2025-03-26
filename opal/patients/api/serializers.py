"""This module provides Django REST framework serializers for PatietnView api return value."""
from rest_framework import serializers

from opal.caregivers.models import RegistrationCode
from opal.core.api.serializers import DynamicFieldsSerializer
from opal.patients.models import HospitalPatient, Patient, Relationship


class HospitalPatientRegistrationSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active']


class PatientSerializer(DynamicFieldsSerializer):
    """Patient serializer used to get patient information."""

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'sex', 'ramq']


class HospitalPatientInstitutionSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get institution information."""

    institution_id = serializers.IntegerField(
        source='site.institution.id',
        read_only=True,
    )

    name = serializers.CharField(
        source='site.institution.name',
        read_only=True,
    )

    class Meta:
        model = HospitalPatient
        fields = ['institution_id', 'name']


class HospitalPatientSiteSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get site information."""

    site_code = serializers.CharField(
        source='site.code',
        read_only=True,
    )

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'site_code']


class CaregiverPatientSerializer(serializers.ModelSerializer):
    """Serializer for the list of patients for a given caregiver."""

    patient_id = serializers.IntegerField(source='patient.id')
    patient_legacy_id = serializers.IntegerField(source='patient.legacy_id')
    first_name = serializers.CharField(source='patient.first_name')
    last_name = serializers.CharField(source='patient.last_name')

    class Meta:
        model = Relationship
        fields = ['patient_id', 'patient_legacy_id', 'first_name', 'last_name', 'status']


class RegistrationCodePatientSerializer(serializers.ModelSerializer):
    """Serializer for the return summary info of registration code."""

    patient = PatientSerializer(
        source='relationship.patient',
        fields=('first_name', 'last_name'),
        many=False,
        read_only=True,
    )
    institutions = HospitalPatientInstitutionSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'institutions']


class RegistrationCodePatientDetailedSerializer(serializers.ModelSerializer):
    """Serializer for the return detailed info of registration code."""

    patient = PatientSerializer(
        source='relationship.patient',
        many=False,
        read_only=True,
    )
    hosptial_patients = HospitalPatientSiteSerializer(
        source='relationship.patient.hospital_patients',
        many=True,
        read_only=True,
    )

    class Meta:
        model = RegistrationCode
        fields = ['patient', 'hosptial_patients']
