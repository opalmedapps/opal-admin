from typing import Optional
from django.contrib import admin
from django.http import HttpRequest

from .models import AbstractSample, HealthDataStore, QuantitySample


class AbstractSampleAdminMixin(admin.ModelAdmin):
    def has_change_permission(self, request: HttpRequest, obj: Optional[AbstractSample] = None) -> bool:
        if obj is not None:
            return False

        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request: HttpRequest, obj: Optional[AbstractSample] = None) -> bool:
        return False


@admin.register(QuantitySample)
class QuantitySampleAdmin(AbstractSampleAdminMixin, admin.ModelAdmin):
    list_display = ['__str__', 'data_store', 'type', 'start_date', 'source', 'added_at']


admin.site.register(HealthDataStore, admin.ModelAdmin)
