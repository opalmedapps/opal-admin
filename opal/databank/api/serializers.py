"""Serializers for the API views of the `databank` app."""
from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import DatabankConsent


class DatabankConsentSerializer(DynamicFieldsSerializer):
    """Serializer for DatabankConsents."""

    # Non model fields used for GUID generation
    middle_name = serializers.CharField(required=True, allow_blank=True, write_only=True)
    city_of_birth = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = DatabankConsent
        fields = [
            'has_appointments',
            'has_diagnoses',
            'has_demographics',
            'has_labs',
            'has_questionnaires',
            'middle_name',
            'city_of_birth',
        ]
