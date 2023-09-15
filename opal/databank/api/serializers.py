"""Serializers for the API views of the `databank` app."""

from rest_framework import serializers
from ..models import DataModuleType, DatabankConsent


class DatabankConsentSerializer(serializers.ModelSerializer):
    """Serializer supporting the creation of a `DatabankConsent` instance."""

    modules = serializers.MultipleChoiceField(choices=DataModuleType.choices, write_only=True)

    class Meta:
        model = DatabankConsent
        fields = ('patient', 'guid', 'has_appointments', 'has_diagnoses', 'has_demographics', 'has_labs', 'has_questionnaires', 'modules')
        read_only_fields = ('patient', 'guid')

    def validate_modules(self, value):
        """Validate module list parameter"""
        return [module.lower() for module in value]

    def create(self, validated_data):
        modules = validated_data.pop('modules', [])
        for module in modules:
            if module in DataModuleType:
                field_name = f'has_{module}'
                validated_data[field_name] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        modules = validated_data.pop('modules', [])
        for module_name, _ in DataModuleType.choices:
            field_name = f'has_{module_name.lower()}'
            setattr(instance, field_name, module_name in modules)
        return super().update(instance, validated_data)
