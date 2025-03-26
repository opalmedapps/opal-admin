"""This module provides admin options for health data models."""
from typing import Optional

from django.contrib import admin
from django.http import HttpRequest

from .models import AbstractSample, HealthDataStore, QuantitySample


class AbstractSampleAdminMixin(admin.ModelAdmin):
    """
    Mixin for sample models to prevent changing an existing instance.

    All admin classes for samples should inherit from this mixin.
    """

    def has_change_permission(self, request: HttpRequest, obj: Optional[AbstractSample] = None) -> bool:
        """
        Return whether the given request has permission to change the given sample instance.

        Changing an existing instance is not permitted.

        Args:
            request: the current HTTP request
            obj: the current instance. Defaults to None.

        Returns:
            `True`, if the instance can be changed, `False` otherwise
        """
        if obj is not None:
            return False

        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request: HttpRequest, obj: Optional[AbstractSample] = None) -> bool:
        """
        Return whether the given request has permission to delete the given sample instance.

        Always returns `False` (deletion is not permitted).

        Args:
            request: the current HTTP request
            obj: the current instance. Defaults to None.

        Returns:
            `False`
        """
        return False


@admin.register(QuantitySample)
class QuantitySampleAdmin(AbstractSampleAdminMixin, admin.ModelAdmin):
    """The admin class for `QuantitySample` models."""

    list_display = [
        '__str__',
        'data_store',
        'type',
        'start_date',
        'source',
        'device',
        'added_at',
    ]


admin.site.register(HealthDataStore, admin.ModelAdmin)
