"""This module provides admin options for patient models."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from .models import Patient, Relationship, RelationshipType


class PatientAdmin(TranslationAdmin):
    """This class provides admin options for `Patient`."""

    pass  # noqa: WPS420, WPS604


class RelationshipAdmin(TranslationAdmin):
    """This class provides admin options for `Relationship`."""

    pass  # noqa: WPS420, WPS604


class RelationshipTypeAdmin(TranslationAdmin):
    """This class provides admin options for `RelationshipType`."""

    pass  # noqa: WPS420, WPS604


admin.site.register(Patient, PatientAdmin)
admin.site.register(Relationship, RelationshipAdmin)
admin.site.register(RelationshipType, RelationshipTypeAdmin)
