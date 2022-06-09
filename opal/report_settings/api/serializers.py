"""This module provides Django REST framework serializers for the report settings models."""

from rest_framework import serializers


class QuestionnaireReportRequestSerializer(serializers.Serializer):
    """This class defines how a `QuestionnairesReport` request data are serialized."""

    patient_id = serializers.IntegerField()
    language = serializers.CharField(min_length=2)
