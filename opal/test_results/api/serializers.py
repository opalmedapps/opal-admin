"""This module provides Django REST framework serializers related to the `test_results` app's models."""
from typing import Any

from django.db import transaction

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.test_results.models import GeneralTest, Note, PathologyObservation


class GeneralTestSerializer(DynamicFieldsSerializer):
    """Serializer for the `GeneralTest` model."""

    class Meta:
        model = GeneralTest
        fields = (
            'patient',
            'type',
            'sending_facility',
            'receiving_facility',
            'collected_at',
            'received_at',
            'message_type',
            'message_event',
            'test_group_code',
            'test_group_code_description',
            'legacy_document_id',
            'case_number',
            'reported_at',
        )


class PathologyObservationSerializer(DynamicFieldsSerializer):
    """Serializer for the `PathologyObservation` model."""

    class Meta:
        model = PathologyObservation
        fields = (
            'general_test',
            'identifier_code',
            'identifier_text',
            'value',
            'observed_at',
            'updated_at',
        )


class NoteSerializer(DynamicFieldsSerializer):
    """Serializer for the `Note` model."""

    class Meta:
        model = Note
        fields = (
            'general_test',
            'note_source',
            'note_text',
            'updated_at',
        )


class PathologySerializer(GeneralTestSerializer):
    """Serializer for the `GeneralTest` (a.k.a. pathology) data received from the `pathology create` endpoint."""

    observations = PathologyObservationSerializer(
        fields=(
            'identifier_code',
            'identifier_text',
            'value',
            'observed_at',
            'updated_at',
        ),
        many=True,
        allow_empty=False,
        required=True,
    )
    notes = NoteSerializer(
        fields=('note_source', 'note_text', 'updated_at'),
        many=True,
        allow_empty=False,
        required=True,
    )

    class Meta:
        model = GeneralTest
        fields = (
            'observations',
            'notes',
            'sending_facility',
            'receiving_facility',
            'collected_at',
            'received_at',
            'message_type',
            'message_event',
            'test_group_code',
            'test_group_code_description',
            'case_number',
            'reported_at',
        )

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> GeneralTest:
        """
        Create new `GeneralTest` record.

        Args:
            validated_data: validated `GeneralTest` data

        Returns:
            the created `GeneralTest` record
        """
        validated_observations = validated_data.pop('observations')
        validated_notes = validated_data.pop('notes')

        general_test = GeneralTest.objects.create(**validated_data)
        PathologyObservation.objects.bulk_create(
            PathologyObservation(**data, general_test=general_test) for data in validated_observations
        )
        Note.objects.bulk_create(
            Note(**data, general_test=general_test) for data in validated_notes
        )

        return general_test
