"""This module provides admin options for patient models."""
from typing import Optional

from django.contrib import admin
from django.http import HttpRequest

from modeltranslation.admin import TranslationAdmin

from . import models


class RelationshipTypeAdmin(TranslationAdmin):
    """This class provides admin options for `RelationshipType`."""

    readonly_fields = ['role_type']

    # Django Admin deletion privileges discussion:
    # https://stackoverflow.com/questions/38127581/django-admin-has-delete-permission-ignored-for-delete-action
    def has_delete_permission(self, request: HttpRequest, obj: Optional[models.RelationshipType] = None) -> bool:
        """Override default default permission behaviour for restricted role types.

        Args:
            request: Http request details.
            obj: The relationship type object to be deleted.

        Returns:
            boolean delete permission (false if model has restricted role type).
        """
        if obj and obj.role_type in models.PREDEFINED_ROLE_TYPES:
            return False

        return super().has_delete_permission(request, obj)  # type: ignore[no-any-return]


class PatientAdmin(admin.ModelAdmin):
    """Admin options for the `Patient` model."""

    readonly_fields = ['uuid']


admin.site.register(models.RelationshipType, RelationshipTypeAdmin)
admin.site.register(models.Relationship, admin.ModelAdmin)
admin.site.register(models.HospitalPatient, admin.ModelAdmin)
admin.site.register(models.Patient, PatientAdmin)
