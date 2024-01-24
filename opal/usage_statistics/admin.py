"""This module provides admin options for databank models."""
from django.contrib import admin

from . import models


@admin.register(models.UserAppActivity)
class DailyUserAppActivityAdmin(admin.ModelAdmin):
    """The admin class for `DailyUserAppActivity` models."""

    list_display = [
        '__str__',
        'user_relationship_to_patient',
        'patient',
        'last_login',
        'count_logins',
        'count_checkins',
        'count_documents',
        'count_educational_materials',
        'count_feedback',
        'count_questionnaires_complete',
        'count_labs',
        'count_update_security_answers',
        'count_update_passwords',
        'count_update_language',
        'count_device_ios',
        'count_device_android',
        'count_device_browser',
        'date_added',
    ]


@admin.register(models.PatientDataReceived)
class DailyPatientDataReceivedAdmin(admin.ModelAdmin):
    """The admin class for `DailyPatientDataReceived` models."""

    list_display = [
        '__str__',
        'patient',
        'next_appointment',
        'last_appointment_received',
        'appointments_received',
        'last_document_received',
        'documents_received',
        'last_educational_materials_received',
        'educational_materials_received',
        'last_questionnaire_received',
        'questionnaires_received',
        'last_lab_received',
        'labs_received',
        'date_added',
    ]


@admin.register(models.PatientDemographic)
class PatientDemographicAdmin(admin.ModelAdmin):
    """The admin class for `PatientDemographic` models."""

    list_display = [
        '__str__',
        'patient',
        'sex',
        'language',
        'access_level',
        'blocked_status',
        'status_reason',
        'completed_registration',
        'date_added',
    ]
