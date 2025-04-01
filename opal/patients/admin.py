# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides admin options for patient models."""

from django.contrib import admin
from django.http import HttpRequest

from modeltranslation.admin import TranslationAdmin

from . import models


@admin.register(models.HospitalPatient)
class HospitalPatientAdmin(admin.ModelAdmin[models.HospitalPatient]):
    """Admin options for the `HospitalPatient` model."""

    list_display = ['__str__', 'mrn', 'site', 'is_active', 'patient']
    list_select_related = ['patient', 'site']
    list_filter = ['site']


@admin.register(models.Patient)
class PatientAdmin(admin.ModelAdmin[models.Patient]):
    """Admin options for the `Patient` model."""

    list_display = ['__str__', 'date_of_birth', 'date_of_death', 'sex', 'ramq', 'data_access', 'legacy_id', 'uuid']
    list_filter = ['sex', 'date_of_birth', 'date_of_death', 'data_access']
    readonly_fields = ['uuid']
    search_fields = ['first_name', 'last_name', 'ramq']


@admin.register(models.RelationshipType)
class RelationshipTypeAdmin(TranslationAdmin[models.RelationshipType]):
    """This class provides admin options for `RelationshipType`."""

    list_display = [
        '__str__',
        'description',
        'start_age',
        'end_age',
        'form_required',
        'can_answer_questionnaire',
        'role_type',
    ]
    readonly_fields = ['role_type']

    # Django Admin deletion privileges discussion:
    # https://stackoverflow.com/questions/38127581/django-admin-has-delete-permission-ignored-for-delete-action
    def has_delete_permission(self, request: HttpRequest, obj: models.RelationshipType | None = None) -> bool:
        """
        Override default default permission behaviour for restricted role types.

        Args:
            request: Http request details.
            obj: The relationship type object to be deleted.

        Returns:
            boolean delete permission (false if model has restricted role type).
        """
        if obj and obj.role_type in models.PREDEFINED_ROLE_TYPES:
            return False

        return super().has_delete_permission(request, obj)


@admin.register(models.Relationship)
class RelationshipAdmin(admin.ModelAdmin[models.Relationship]):
    """Admin options for the `Relationship` model."""

    date_hierarchy = 'request_date'
    list_display = ['__str__', 'patient', 'caregiver', 'type', 'status', 'request_date', 'start_date', 'end_date']
    list_select_related = ['patient', 'caregiver', 'caregiver__user', 'type']
    list_filter = ['type', 'status']
