"""This module provides admin options for health data models."""
from django.contrib import admin
from django.contrib.admin.options import BaseModelAdmin
from django.http import HttpRequest

from .models import AbstractSample, QuantitySample


class AbstractSampleAdminMixin(BaseModelAdmin[AbstractSample]):
    """
    Mixin for sample models to prevent changing an existing instance.

    All admin classes for samples should inherit from this mixin.
    """

    def has_change_permission(self, request: HttpRequest, obj: AbstractSample | None = None) -> bool:
        """
        Return whether the given request has permission to change the given sample instance.

        Always returns `False` (changes not permitted).

        Args:
            request: the current HTTP request
            obj: the current instance. Defaults to None.

        Returns:
            `False`
        """
        return False

    def has_delete_permission(self, request: HttpRequest, obj: AbstractSample | None = None) -> bool:
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
class QuantitySampleAdmin(AbstractSampleAdminMixin, admin.ModelAdmin[QuantitySample]):
    """The admin class for `QuantitySample` models."""

    list_display = [
        '__str__',
        'patient',
        'type',
        'start_date',
        'source',
        'device',
        'added_at',
        'viewed_at',
        'viewed_by',
    ]
