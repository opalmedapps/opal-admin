# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializers for the API views of the `health_data` app."""

from typing import Any

from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from opal.services.fhir.utils import validate_observation

from ..models import PatientReportedData, QuantitySample


class QuantitySampleListSerializer(serializers.ListSerializer[list[QuantitySample]]):
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


def _validate_observation(value: dict[str, Any]) -> None:
    """
    Validate that the given value is a valid FHIR `Observation` resource.

    Args:
        value: the value to validate

    Raises:
        ValidationError: if the value is not a valid `Observation`
    """
    try:
        validate_observation(value).model_dump(mode='json')
    except PydanticValidationError as exc:
        errors = [
            {
                'loc': error['loc'],
                'msg': error['msg'],
                'type': error['type'],
            }
            for error in exc.errors()
        ]

        raise serializers.ValidationError(errors) from exc  # type: ignore[arg-type]


class PatientReportedDataSerializer(serializers.ModelSerializer[PatientReportedData]):
    """Serializer for `PatientReportedData` instances."""

    social_history = serializers.ListField(
        child=serializers.JSONField(validators=[_validate_observation]),
        required=False,
        allow_null=False,
        default=list,
        allow_empty=True,
    )

    class Meta:
        model = PatientReportedData
        fields = ('social_history',)
