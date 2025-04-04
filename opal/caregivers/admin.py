# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing admin functionality for the caregivers app."""

from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from . import models


@admin.register(models.CaregiverProfile)
class CaregiverProfileAdmin(admin.ModelAdmin[models.CaregiverProfile]):
    """Admin options for the `CaregiverProfile` model."""

    list_display = ['__str__', 'uuid', 'legacy_id', 'user']
    readonly_fields = ['uuid']
    # select_related for the actual user with first and last name
    list_select_related = ['user']


@admin.register(models.Device)
class DeviceAdmin(admin.ModelAdmin[models.Device]):
    """Admin options for the `Device` model."""

    list_display = ['__str__', 'type', 'is_trusted', 'modified', 'caregiver']
    list_filter = ['type', 'modified']


@admin.register(models.EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin[models.EmailVerification]):
    """Admin options for the `EmailVerification` model."""

    list_display = ['__str__', 'email', 'is_verified', 'sent_at', 'caregiver']
    list_filter = ['is_verified', 'sent_at']


@admin.register(models.RegistrationCode)
class RegistrationCodeAdmin(admin.ModelAdmin[models.RegistrationCode]):
    """Admin options for the `RegistrationCode` model."""

    list_display = ['__str__', 'status', 'created_at', 'attempts', 'relationship']
    list_filter = ['created_at', 'status']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']


@admin.register(models.SecurityAnswer)
class SecurityAnswerAdmin(admin.ModelAdmin[models.SecurityAnswer]):
    """Admin options for the `SecurityAnswer` model."""

    list_display = ['question', 'user']
    search_fields = ['question', 'user__user__first_name', 'user__user__last_name']
    # select_related for the actual user with first and last name
    list_select_related = ['user__user']


@admin.register(models.SecurityQuestion)
class SecurityQuestionAdmin(TranslationAdmin[models.SecurityQuestion]):
    """This class provides admin options for `SecurityQuestion`."""

    list_display = ['__str__', 'is_active']
