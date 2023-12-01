"""This module provides admin options for databank models."""
from django.contrib import admin

from . import models


@admin.register(models.DatabankConsent)
class DatabankConsentAdmin(admin.ModelAdmin[models.DatabankConsent]):
    """The admin class for `DatabankConsent` models."""

    list_display = [
        '__str__',
        'has_appointments',
        'has_diagnoses',
        'has_demographics',
        'has_labs',
        'has_questionnaires',
        'consent_granted',
        'last_synchronized',
    ]
