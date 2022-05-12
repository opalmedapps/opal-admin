"""This module provides admin options for patient models."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from .models import RelationshipType


class RelationshipTypeAdmin(TranslationAdmin):
    """This class provides admin options for `RelationshipType`."""

    pass  # noqa: WPS420, WPS604


admin.site.register(RelationshipType, RelationshipTypeAdmin)
