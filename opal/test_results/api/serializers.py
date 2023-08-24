"""This module provides Django REST framework serializers related to the `test_results` app's models."""
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.patients.models import Patient
from opal.test_results.models import GeneralTest, Note, Observation


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


class ObservationSerializer(DynamicFieldsSerializer):
    """Serializer for the `Observation` model."""

    class Meta:
        model = Observation
        fields = (
            'general_test',
            'identifier_code',
            'identifier_text',
            'value',
            'value_units',
            'value_min_range',
            'value_max_range',
            'value_abnormal',
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


class PatientUUIDRelatedField(serializers.RelatedField):
    """Custom patient UUID relational field that describes how the output representation should be generated."""

    default_error_messages = {
        'empty_queryset': 'Empty queryset. Expected a `QuerySet[Patient]`.',
        'incorrect_queryset_type': 'Incorrect queryset type. Expected a `QuerySet[Patient]`, but got {queryset_type}',
        'does_not_exist': 'Invalid UUID "{value}" - patient does not exist.',
    }

    def to_representation(self, value: Patient) -> str:
        """Convert a `Patient` instance into patient's UUID string (i.e., into primitive, serializable datatype).

        Args:
            value: patient object to be converted

        Returns:
            UUID of a patient
        """
        return str(value.uuid)

    def to_internal_value(self, data: str) -> Patient:
        """Restore a patient's UUID into `Patient` object representation.

        Takes the unvalidated incoming data as input and should return the validated data.

        Args:
            data: UUID of a patient that has to be found

        Returns:
            found patient
        """
        if not self.queryset:
            self.fail('empty_queryset')

        if self.queryset.model is not Patient:
            self.fail('incorrect_queryset_type', queryset_type=self.queryset.model)

        # Check that `patient` with given UUID exists in the database.
        try:
            patient: Patient = self.queryset.get(uuid=data)
        except ObjectDoesNotExist:
            # Raise ValidationError if patient does not exist.
            self.fail('does_not_exist', value=data)

        return patient


class PathologySerializer(GeneralTestSerializer):
    """Serializer for the `GeneralTest` (a.k.a. pathology) data received from the `pathology create` endpoint."""

    patient = PatientUUIDRelatedField(queryset=Patient.objects.all())
    observations = ObservationSerializer(
        fields=(
            'identifier_code',
            'identifier_text',
            'value',
            'value_units',
            'value_min_range',
            'value_max_range',
            'value_abnormal',
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
            'patient',
            'observations',
            'notes',
            'type',
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
        Observation.objects.bulk_create(
            Observation(**data, general_test=general_test) for data in validated_observations
        )
        Note.objects.bulk_create(
            Note(**data, general_test=general_test) for data in validated_notes
        )

        return general_test
