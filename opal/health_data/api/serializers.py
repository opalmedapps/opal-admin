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


class PatientReportedDataSerializer(serializers.ModelSerializer[PatientReportedData]):
    """Serializer for `PatientReportedData` instances."""

    def _validate_observation(self, value: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that the given value is a valid FHIR `Observation` resource.

        Args:
            value: the value to validate

        Returns:
            the validated value if it is a valid `Observation`

        Raises:
            ValidationError: if the value is not a valid `Observation`
        """
        try:
            observation: dict[str, Any] = validate_observation(value).model_dump(mode='json')
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

        return observation

    def validate_alcohol_use(self, value: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        Validate the `alcohol_use` field.

        Raises a `ValidationError` if the value is not a valid FHIR `Observation` resource.

        Args:
            value: the value of the `alcohol_use` field to validate

        Returns:
            the validated value
        """
        if value is None:
            return value

        return self._validate_observation(value)

    def validate_tobacco_use(self, value: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        Validate the `tobacco_use` field.

        Raises a `ValidationError` if the value is not a valid FHIR `Observation` resource.

        Args:
            value: the value of the `tobacco_use` field to validate

        Returns:
            the validated value
        """
        if value is None:
            return value

        return self._validate_observation(value)

    class Meta:
        model = PatientReportedData
        fields = ('alcohol_use', 'tobacco_use')
