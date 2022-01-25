"""This module provides admin options for hospital-specific settings models."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from .models import Institution, Site


# need to use modeltranslation's admin
# see: https://django-modeltranslation.readthedocs.io/en/latest/admin.html
class InstitutionAdmin(TranslationAdmin):
    """This class provides admin options for ``Institution``."""

    pass  # noqa: WPS420, WPS604


class SiteAdmin(TranslationAdmin):
    """This class provides admin options for ``Site``."""

    pass  # noqa: WPS420, WPS604


admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Site, SiteAdmin)
