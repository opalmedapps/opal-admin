"""This module provides Django REST framework serializers related to the `patients` app's models."""
from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.patients.models import HospitalPatient, Patient, Relationship


class PatientSerializer(DynamicFieldsSerializer):
    """Patient serializer used to get patient information."""

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'sex', 'ramq']


class HospitalPatientSerializer(DynamicFieldsSerializer):
    """Hospital patient serializer used to get Hospital patient information."""

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active']


class HospitalPatientAndSiteSerializer(serializers.ModelSerializer):
    """Hospital patient serializer which also provides the site code."""

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
