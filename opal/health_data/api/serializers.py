"""Serializers for the API views of the `health_data` app."""
from typing import Any

from rest_framework import serializers

from ..models import QuantitySample


class QuantitySampleListSerializer(serializers.ListSerializer):
    """List serializer supporting the bulk creation of multiple `QuantitySample` instances."""

    def create(self, validated_data: list[dict[str, Any]]) -> list[QuantitySample]:
        """
        Bulk create new `QuantitySample` instances.

        The samples are created for the patient that is provided in the serializer context.

        Args:
            validated_data: a list of validated data dictionaries

        Returns:
            the list of created `QuantitySample` instances
        """
        # add patient reference to each element
        for element in validated_data:
            element['patient'] = self.context['patient']

        return QuantitySample.objects.bulk_create(QuantitySample(**data) for data in validated_data)


class QuantitySampleSerializer(serializers.ModelSerializer[QuantitySample]):
    """
    Serializer for `QuantitySample` instances.

    It supports the creation of multiple instances by passing a list of dictionaries using a list serializer.
    See: https://www.django-rest-framework.org/api-guide/serializers/#customizing-listserializer-behavior
    """

    def create(self, validated_data: dict[str, Any]) -> QuantitySample:
        """
        Create a new `QuantitySample` instance.

        The sample is created for the patient that is provided in the serializer context.

        Args:
            validated_data: the validated data dictionary

        Returns:
            the newly created `QuantitySample` instance
        """
        # add patient reference to create a new instance
        validated_data['patient'] = self.context['patient']

        return super().create(validated_data)

    class Meta:
        model = QuantitySample
        fields = ('type', 'value', 'start_date', 'device', 'source')
        # See: https://www.django-rest-framework.org/api-guide/serializers/#customizing-multiple-create
        list_serializer_class = QuantitySampleListSerializer
