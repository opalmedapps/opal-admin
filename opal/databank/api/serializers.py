"""This module provides Django REST framework serializers related to the `databank` data models."""

from rest_framework import serializers


class AppointmentDataSerializer(serializers.Serializer):
    """Serializer for databank appointment data."""

    appointment_id = serializers.IntegerField()
    date_created = serializers.DateTimeField()
    source_db_name = serializers.CharField()
    source_db_alias_code = serializers.CharField()
    source_db_alias_description = serializers.CharField()
    source_db_appointment_id = serializers.IntegerField()
    alias_name = serializers.CharField()
    scheduled_start_time = serializers.DateTimeField()
    scheduled_end_time = serializers.DateTimeField()
    last_updated = serializers.DateTimeField()


class DiagnosisDataSerializer(serializers.Serializer):
    """Serializer for databank diagnosis data."""

    diagnosis_id = serializers.IntegerField()
    date_created = serializers.DateTimeField()
    stage = serializers.CharField()
    stage_criteria = serializers.CharField()
    source_system_code = serializers.CharField()
    source_system_code_description = serializers.CharField()
    last_updated = serializers.DateTimeField()


class DemographicsDataSerializer(serializers.Serializer):
    """Serializer for databank demographics data."""

    patient_id = serializers.IntegerField()
    patient_sex = serializers.CharField()
    patient_birth_date = serializers.DateField()
    patient_death_date = serializers.DateField(allow_null=True)
    patient_primary_language = serializers.CharField()
    date_created = serializers.DateTimeField()
    last_updated = serializers.DateTimeField()


class LabComponentSerializer(serializers.Serializer):
    """Serializer for a lab component, used by LabsDataSerializer."""

    test_result_id = serializers.CharField()
    specimen_collected_date = serializers.DateTimeField()
    component_result_date = serializers.DateTimeField()
    test_component_sequence = serializers.CharField()
    test_component_name = serializers.CharField()
    test_value = serializers.CharField()
    test_units = serializers.CharField()
    max_norm_range = serializers.CharField()
    min_norm_range = serializers.CharField()
    abnormal_flag = serializers.CharField()
    source_system = serializers.CharField()
    last_updated = serializers.DateTimeField()


class LabsDataSerializer(serializers.Serializer):
    """Serializer for databank labs data."""

    GUID = serializers.CharField()  # noqa: WPS115
    test_group_name = serializers.CharField()
    test_group_indicator = serializers.CharField()
    components = LabComponentSerializer(many=True)


class QuestionnaireDataSerializer(serializers.Serializer):
    """Serializer for databank labs data."""

    answer_questionnaire_id = serializers.IntegerField()
    creation_date = serializers.DateTimeField()
    questionnaire_id = serializers.IntegerField()
    questionnaire_title = serializers.CharField()
    question_id = serializers.IntegerField()
    question_text = serializers.CharField()
    question_display_order = serializers.IntegerField()
    question_type_id = serializers.IntegerField()
    question_type_text = serializers.CharField()
    question_answer_id = serializers.IntegerField()
    last_updated = serializers.DateTimeField()
    answer_value = serializers.CharField()
