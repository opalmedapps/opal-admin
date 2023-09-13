"""This module provides admin options for test result models."""
from django.contrib import admin

from .models import GeneralTest, Note, Observation


@admin.register(GeneralTest)
class GeneralTestAdmin(admin.ModelAdmin):
    """The admin class for `GeneralTest` models."""

    list_display = ('patient', 'type', 'collected_at', 'received_at', 'reported_at')
    list_filter = ('type',)
    search_fields = (
        'patient__first_name',
        'patient__last_name',
        'patient__ramq',
        'sending_facility',
        'receiving_facility',
    )
    ordering = ('patient', '-collected_at')


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    """The admin class for `Observation` models."""

    list_display = (
        'general_test',
        'identifier_code',
        'value',
        'observed_at',
        'updated_at',
    )
    list_filter = ('general_test',)
    search_fields = (
        'general_test__patient__first_name',
        'general_test__patient__last_name',
        'general_test__patient__ramq',
        'identifier_code',
        'identifier_text',
    )
    ordering = ('general_test', '-updated_at')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """The admin class for `Note` models."""

    list_display = ('note_text', 'general_test', 'note_source', 'updated_at')
    list_filter = ('general_test',)
    search_fields = (
        'general_test__patient__first_name',
        'general_test__patient__last_name',
        'general_test__patient__ramq',
        'note_source',
        'note_text',
    )
    ordering = ('general_test', '-updated_at')
