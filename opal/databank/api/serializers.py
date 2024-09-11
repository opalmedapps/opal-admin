"""Serializers for the API views of the `databank` app."""
from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import DatabankConsent


class DatabankConsentSerializer(DynamicFieldsSerializer[DatabankConsent]):
    """Serializer for DatabankConsents."""

    # Non model fields used for GUID generation
    middle_name = serializers.CharField(required=True, allow_blank=True, write_only=True)
    city_of_birth = serializers.CharField(required=True, write_only=True)
    # Non model fields collected in consent form, used for checking specific authorizations
    health_data_authorization = serializers.CharField(write_only=True)
    contact_authorization = serializers.CharField(write_only=True)

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
            'health_data_authorization',
            'contact_authorization',
        ]

    def validate_health_data_authorization(self, value: str) -> str:
        """
        Validate the health_data_authorization field to ensure it is 'Consent'.

        Args:
            value: Response to the Health Data authorization consent form question

        Returns:
            validated health_data_authorization

        Raises:
            ValidationError: if patient declined authorization

        """
        if value != 'Consent':
            raise serializers.ValidationError("Health data authorization must be 'Consent'.")
        return value

    def validate_contact_authorization(self, value: str) -> str:
        """
        Validate the contact_authorization field to ensure it is 'Consent'.

        Args:
            value: Response to the Contact authorization consent form question

        Returns:
            validated contact_authorization

        Raises:
            ValidationError: if patient declined authorization

        """
        if value != 'Consent':
            raise serializers.ValidationError("Contact authorization must be 'Consent'.")
        return value
