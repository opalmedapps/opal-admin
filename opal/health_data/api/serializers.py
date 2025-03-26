"""Serializers for the API views of the `health_data` app."""
from typing import Any

from rest_framework import serializers

from ..models import QuantitySample


class QuantitySampleListSerializer(serializers.ListSerializer):
    """List serializer supporting the bulk creation of multiple `QuantitySample` instances."""

    def create(self, validated_data: list[dict[str, Any]]) -> list[QuantitySample]:
        """
        Bulk create new `QuantitySample` instances.

        The patient for which the samples are created needs to be passed to `serializer.save()` as an extra argument.

        Args:
            validated_data: a list of validated data dictionaries

        Returns:
            the list of created `QuantitySample` instances
        """
        return QuantitySample.objects.bulk_create(QuantitySample(**data) for data in validated_data)


class QuantitySampleSerializer(serializers.ModelSerializer[QuantitySample]):
    """
    Serializer for `QuantitySample` instances.

    The patient for which the samples are created needs to be passed to `serializer.save()` as an extra argument.

    It supports the creation of multiple instances by passing a list of dictionaries using a list serializer.
    See: https://www.django-rest-framework.org/api-guide/serializers/#customizing-listserializer-behavior
    """

    class Meta:
        model = QuantitySample
        fields = ('type', 'value', 'start_date', 'device', 'source')
        # See: https://www.django-rest-framework.org/api-guide/serializers/#customizing-multiple-create
        list_serializer_class = QuantitySampleListSerializer
