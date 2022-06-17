"""This module provides Django REST framework serializers for the report settings models."""

from django.conf import settings

from rest_framework import serializers


class QuestionnaireReportRequestSerializer(serializers.Serializer):
    """This class defines how a `QuestionnairesReport` request data are serialized."""

    patient_id = serializers.IntegerField()
    language = serializers.CharField(min_length=2)

    # def validate_patient_id(self, value):
    #     """
    #     Check that patient id exists in the OpalDB.
    #     """

    #     TODO: check if requested id exists

    def validate_language(self, language_field: str) -> str:
        """
        Check that requested language exists.

        Args:
            language_field: Requested language of the report

        Returns:
            Validated language field value

        Raises:
            ValidationError: Exception
        """
        for lang in settings.LANGUAGES:
            if lang[0].lower() == language_field.lower():
                return language_field

        raise serializers.ValidationError('Requested language is not supported.')
