"""Module that contains serializer classes for patient models."""

from rest_framework import serializers
from opal.patients.models import HospitalPatient, Patient, Relationship


class PatientDetailSerializer(serializers.ModelSerializer):
    """Patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'sex', 'ramq']


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """Patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = Patient
        fields = ['ramq']


class HospitalPatientRegistrationSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active']


class HospitalInstitutionSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get encryption values for registration web site."""

    id = serializers.PrimaryKeyRelatedField(
        source='site.institution.id',
        read_only=True,
    )

    name = serializers.CharField(
        source='site.institution.name',
        read_only=True,
    )

    class Meta:
        model = HospitalPatient
        fields = ['id', 'name']


class CaregiverPatientSerializer(serializers.ModelSerializer):
    """Serializer for the list of patients for a given caregiver."""

    patient_id = serializers.IntegerField(source='patient.id')
    patient_legacy_id = serializers.IntegerField(source='patient.legacy_id')
    first_name = serializers.CharField(source='patient.first_name')
    last_name = serializers.CharField(source='patient.last_name')

    class Meta:
        model = Relationship
        fields = ['patient_id', 'patient_legacy_id', 'first_name', 'last_name', 'status']
