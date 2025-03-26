"""Serializers for the API views of the `databank` app."""
from typing import Any

from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import DatabankConsent


class DatabankConsentSerializer(DynamicFieldsSerializer):
    """Serializer for DatabankConsents."""

    # Non model fields used for GUID generation
    middle_name = serializers.CharField(required=True, write_only=True)
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
        read_only_fields = ['patient']

    def create(self, validated_data: dict[str, Any]) -> Any:
        """Create new `DatabankConsent` instance.

        Args:
            validated_data: validated `DatabankConsent` data

        Returns:
            the created `DatabankConsent` record
        """
        # Remove non-model fields
        validated_data.pop('middle_name', None)
        validated_data.pop('city_of_birth', None)
        return super().create(validated_data)
