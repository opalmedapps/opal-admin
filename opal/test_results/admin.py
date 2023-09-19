"""This module provides admin options for test result models."""
from django.contrib import admin

from .models import GeneralTest, Note, PathologyObservation


@admin.register(GeneralTest)
class GeneralTestAdmin(admin.ModelAdmin):
    """The admin class for `GeneralTest` models."""

    list_display = ('patient', 'type', 'collected_at', 'received_at', 'reported_at')
    list_filter = ('type',)
    search_fields = (
        'patient__first_name',
        'patient__last_name',
        'collected_at',
    )
    ordering = ('patient', '-collected_at')


@admin.register(PathologyObservation)
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
        'identifier_code',
        'identifier_text',
        'observed_at',
    )
    ordering = ('general_test', '-observed_at')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """The admin class for `Note` models."""

    list_display = ('general_test', 'note_text', 'note_source', 'updated_at')
    list_filter = ('general_test',)
    search_fields = (
        'general_test__patient__first_name',
        'general_test__patient__last_name',
        'note_source',
        'note_text',
    )
    ordering = ('general_test', '-updated_at')
