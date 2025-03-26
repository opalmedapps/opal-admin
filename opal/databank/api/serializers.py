"""Serializers for the API views of the `databank` app."""
from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import DatabankConsent


class DatabankConsentSerializer(DynamicFieldsSerializer):
    """Serializer for DatabankConsents."""

    class Meta:
        model = DatabankConsent
        fields = [
            'has_appointments',
            'has_diagnoses',
            'has_demographics',
            'has_labs',
            'has_questionnaires',
        ]
