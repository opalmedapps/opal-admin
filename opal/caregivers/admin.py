"""Module providing admin functionality for the caregivers app."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from . import models


class SecurityQuestionAdmin(TranslationAdmin):
    """This class provides admin options for `SecurityQuestion`."""

    pass  # noqa: WPS420, WPS604


admin.site.register(models.CaregiverProfile, admin.ModelAdmin)
admin.site.register(models.RegistrationCode, admin.ModelAdmin)
admin.site.register(models.SecurityQuestion, SecurityQuestionAdmin)
admin.site.register(models.SecurityAnswer, admin.ModelAdmin)
