# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides admin options for usage statistics models."""

from django.contrib import admin

from .models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity


@admin.register(DailyUserAppActivity)
class DailyUserAppActivityAdmin(admin.ModelAdmin[DailyUserAppActivity]):
    """The admin class for `DailyUserAppActivity` models."""

    list_display = [
        '__str__',
        'last_login',
        'count_logins',
        'count_feedback',
        'count_update_security_answers',
        'count_update_passwords',
        'count_update_language',
        'count_device_ios',
        'count_device_android',
        'count_device_browser',
        'action_date',
    ]


@admin.register(DailyUserPatientActivity)
class DailyUserPatientActivityAdmin(admin.ModelAdmin[DailyUserPatientActivity]):
    """The admin class for `DailyUserPatientActivity` models."""

    list_display = [
        '__str__',
        'user_relationship_to_patient',
        'patient',
        'count_checkins',
        'count_documents',
        'count_educational_materials',
        'count_questionnaires_complete',
        'count_labs',
        'action_date',
    ]


@admin.register(DailyPatientDataReceived)
class DailyPatientDataReceivedAdmin(admin.ModelAdmin[DailyPatientDataReceived]):
    """The admin class for `DailyPatientDataReceived` models."""

    list_display = [
        '__str__',
        'patient',
        'next_appointment',
        'last_appointment_received',
        'appointments_received',
        'last_document_received',
        'documents_received',
        'last_educational_material_received',
        'educational_materials_received',
        'last_questionnaire_received',
        'questionnaires_received',
        'last_lab_received',
        'labs_received',
        'action_date',
    ]
