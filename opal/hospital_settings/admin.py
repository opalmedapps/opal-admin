"""This module provides admin options for hospital-specific settings models."""
from django.contrib import admin
from django.http import HttpRequest

from modeltranslation.admin import TranslationAdmin

from .models import Institution, Site


# need to use modeltranslation's admin
# see: https://django-modeltranslation.readthedocs.io/en/latest/admin.html
class InstitutionAdmin(TranslationAdmin, admin.ModelAdmin):
    """This class provides admin options for `Institution`."""

    list_display = ['__str__', 'acronym']

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Return whether the given request has permission to add a new institution.

        Returns `False` if an institution already exists.

        Args:
            request: the current HTTP request

        Returns:
            `True` if no institution exists and the user has permissions, `False` otherwise
        """
        if Institution.objects.count() > 0:
            return False

        return super().has_add_permission(request)


class SiteAdmin(TranslationAdmin):
    """This class provides admin options for `Site`."""

    list_display = ['__str__', 'acronym', 'institution']


admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Site, SiteAdmin)
