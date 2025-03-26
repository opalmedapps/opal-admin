"""Module providing admin functionality for the caregivers app."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from . import models


class CaregiverProfileAdmin(admin.ModelAdmin):
    """Admin options for the `CaregiverProfile` model."""

    readonly_fields = ['uuid']


class RegistrationCodeAdmin(admin.ModelAdmin):
    """Admin options for the `RegistrationCode` model."""

    readonly_fields = ['created_at']


class SecurityQuestionAdmin(TranslationAdmin):
    """This class provides admin options for `SecurityQuestion`."""

    pass  # noqa: WPS420, WPS604


admin.site.register(models.CaregiverProfile, CaregiverProfileAdmin)
admin.site.register(models.RegistrationCode, RegistrationCodeAdmin)
admin.site.register(models.SecurityQuestion, SecurityQuestionAdmin)
admin.site.register(models.SecurityAnswer, admin.ModelAdmin)
admin.site.register(models.Device, admin.ModelAdmin)
