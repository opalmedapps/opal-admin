# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides admin options for hospital-specific settings models."""

from django.contrib import admin
from django.http import HttpRequest

from modeltranslation.admin import TranslationAdmin

from .models import Institution, Site


# need to use modeltranslation's admin
# see: https://django-modeltranslation.readthedocs.io/en/latest/admin.html
@admin.register(Institution)
class InstitutionAdmin(TranslationAdmin[Institution]):
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


@admin.register(Site)
class SiteAdmin(TranslationAdmin[Site]):
    """This class provides admin options for `Site`."""

    list_display = ['__str__', 'acronym', 'institution']
