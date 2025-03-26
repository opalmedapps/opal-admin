"""Serializers for the API views of the `health_data` app."""
from typing import Any

from rest_framework import serializers

from opal.patients.models import Patient

from ..models import QuantitySample


class QuantitySampleListSerializer(serializers.ListSerializer):
    """List serializer supporting the bulk creation of multiple `QuantitySample` instances."""

    def create(self, validated_data: list[dict[str, Any]]) -> list[QuantitySample]:
        """
        Bulk create new `QuantitySample` instances.

        Args:
            validated_data: a list of validated data dictionaries

        Returns:
            the list of created `QuantitySample` instances
        """
        return QuantitySample.objects.bulk_create(QuantitySample(**data) for data in validated_data)


class CurrentPatientDefault:
    """
    Callable that extracts the patient from the serializer context.

    See: https://www.django-rest-framework.org/api-guide/fields/#default
    """

    requires_context = True

    def __call__(self, serializer_field: serializers.Field) -> Patient:
        """
        Return the patient from the serializer context.

        Args:
            serializer_field: the serializer field

        Returns:
            the patient
        """
        patient: Patient = serializer_field.context['patient']

        return patient  # noqa: WPS331


class QuantitySampleSerializer(serializers.ModelSerializer[QuantitySample]):
    """
    Serializer for `QuantitySample` instances.

    It supports the creation of multiple instances by passing a list of dictionaries using a list serializer.
    See: https://www.django-rest-framework.org/api-guide/serializers/#customizing-listserializer-behavior
    """

    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        default=CurrentPatientDefault(),
    )

    class Meta:
        model = QuantitySample
        fields = ('patient', 'type', 'value', 'start_date', 'device', 'source')
        # See: https://www.django-rest-framework.org/api-guide/serializers/#customizing-multiple-create
        list_serializer_class = QuantitySampleListSerializer
