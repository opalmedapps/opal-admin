"""This module provides admin options for patient models."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from . import models


class RelationshipTypeAdmin(TranslationAdmin):
    """This class provides admin options for `RelationshipType`."""

    pass  # noqa: WPS420, WPS604


admin.site.register(models.RelationshipType, RelationshipTypeAdmin)
admin.site.register(models.Relationship, admin.ModelAdmin)
admin.site.register(models.HospitalPatient, admin.ModelAdmin)
admin.site.register(models.Patient, admin.ModelAdmin)
