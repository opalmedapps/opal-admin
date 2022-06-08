"""This module provides admin options for report settings models."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from .models import ReportTemplate


# need to use modeltranslation's admin
# see: https://django-modeltranslation.readthedocs.io/en/latest/admin.html
class ReportTemplateAdmin(TranslationAdmin):
    """This class provides admin options for `ReportTemplate`."""

    pass  # noqa: WPS420, WPS604


admin.site.register(ReportTemplate, ReportTemplateAdmin)
