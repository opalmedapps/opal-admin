"""Module that contains serializer classes for patient models."""

from rest_framework import serializers

from opal.patients.models import HospitalPatient, Patient, Relationship


class HospitalPatientRegistrationSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active']


class PatientDetailedSerializer(serializers.ModelSerializer):
    """Patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'sex', 'ramq']


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """Patient serializer used to get encryption values for registration web site."""

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name']


class HospitalInstitutionSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get encryption values for registration web site."""

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


class HospitalSiteSerializer(serializers.ModelSerializer):
    """Hospital patient serializer used to get encryption values for registration web site."""

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
