"""Module providing admin functionality for the caregivers app."""
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from . import models


class CaregiverProfileAdmin(admin.ModelAdmin):
    """Admin options for the `CaregiverProfile` model."""

    list_display = ['__str__', 'uuid', 'legacy_id', 'user']
    readonly_fields = ['uuid', 'user']
    # select_related for the actual user with first and last name
    list_select_related = ['user']


class DeviceAdmin(admin.ModelAdmin):
    """Admin options for the `Device` model."""

    list_display = ['__str__', 'type', 'is_trusted', 'modified', 'caregiver']
    list_filter = ['type', 'modified']


class RegistrationCodeAdmin(admin.ModelAdmin):
    """Admin options for the `RegistrationCode` model."""

    list_display = ['__str__', 'status', 'created_at', 'attempts', 'relationship']
    list_filter = ['created_at', 'status']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']


class SecurityAnswerAdmin(admin.ModelAdmin):
    """Admin options for the `SecurityAnswer` model."""

    list_display = ['question', 'user']
    search_fields = ['question', 'user__user__first_name', 'user__user__last_name']
    # select_related for the actual user with first and last name
    list_select_related = ['user__user']


class SecurityQuestionAdmin(TranslationAdmin):
    """This class provides admin options for `SecurityQuestion`."""

    list_display = ['__str__', 'is_active']


admin.site.register(models.CaregiverProfile, CaregiverProfileAdmin)
admin.site.register(models.RegistrationCode, RegistrationCodeAdmin)
admin.site.register(models.SecurityQuestion, SecurityQuestionAdmin)
admin.site.register(models.SecurityAnswer, SecurityAnswerAdmin)
admin.site.register(models.Device, DeviceAdmin)
