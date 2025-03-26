"""This module provides Django REST framework serializers related to the `patients` app's models."""
from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.patients.models import HospitalPatient, Patient, Relationship


class PatientSerializer(DynamicFieldsSerializer):
    """
    Patient serializer.

    The serializer, which inherits from core.api.serializers.DynamicFieldsSerializer,
    is used to get patient information according to the 'fields' arguments.
    """

    legacy_id = serializers.IntegerField(min_value=1)  # noqa: WPS432

    class Meta:
        model = Patient
        fields = ['legacy_id', 'first_name', 'last_name', 'date_of_birth', 'sex', 'ramq']


class HospitalPatientSerializer(DynamicFieldsSerializer):
    """
    Hospital patient serializer.

    The serializer inherits from core.api.serializers.DynamicFieldsSerializer,
    and also provides HospitalPatient info and the site code according to the 'fields' argumens.
    """

    site_code = serializers.CharField(
        source='site.code',
        read_only=True,
    )

    class Meta:
        model = HospitalPatient
        fields = ['mrn', 'is_active', 'site_code']


class CaregiverPatientSerializer(serializers.ModelSerializer):
    """Serializer for the list of patients for a given caregiver."""

    patient_id = serializers.IntegerField(source='patient.id')
    patient_legacy_id = serializers.IntegerField(source='patient.legacy_id')
    first_name = serializers.CharField(source='patient.first_name')
    last_name = serializers.CharField(source='patient.last_name')

    class Meta:
        model = Relationship
        fields = ['patient_id', 'patient_legacy_id', 'first_name', 'last_name', 'status']


class CaregiverRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for the list of caregivers for a given patient."""

    caregiver_id = serializers.IntegerField(source='caregiver.user.id')
    first_name = serializers.CharField(source='caregiver.user.first_name')
    last_name = serializers.CharField(source='caregiver.user.last_name')

    class Meta:
        model = Relationship
        fields = ['caregiver_id', 'first_name', 'last_name', 'status']
