"""This module provides admin options for patient models."""
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from modeltranslation.admin import TranslationAdmin
from modeltranslation.manager import MultilingualQuerySet

from . import models


class RelationshipTypeAdmin(TranslationAdmin):
    """This class provides admin options for `RelationshipType`."""

    def delete_queryset(self, request: HttpRequest, queryset: MultilingualQuerySet) -> None:
        """Validate that every model in the deletion queryset is not of type 'self' or 'parentguardian'.

        Note: This method is specifically for managing the multi-delete method accesible from the action bar
              of the RelationshipType admin page. There is a separate delete method below for instance deletion.

        Args:
            request: The http request for deletion
            queryset: The set of models to be deleted

        Raises:
            ValidationError: If an operator attempts to delete self or parent guardian - roled relationshiptype.
        """
        for relationship_type in queryset:
            if (relationship_type.role_type in {models.RoleType.SELF, models.RoleType.PARENTGUARDIAN}):
                raise ValidationError(
                    _('Operator cannot delete relationship type with this role'),
                )
        queryset.delete()

    def delete_model(self, request: HttpRequest, instance: models.RelationshipType) -> None:
        """Validate that the model to be deleted is not of type 'self' or 'parentguardian'.

        Args:
            request: The http request for deletion
            instance: The models to be deleted

        Raises:
            ValidationError: If an operator attempts to delete self or parent guardian - roled relationshiptype.
        """
        if (instance.role_type in {models.RoleType.SELF, models.RoleType.PARENTGUARDIAN}):
            raise ValidationError(
                _('Operator cannot delete relationship type with this role'),
            )
        instance.delete()


admin.site.register(models.RelationshipType, RelationshipTypeAdmin)
admin.site.register(models.Relationship, admin.ModelAdmin)
admin.site.register(models.HospitalPatient, admin.ModelAdmin)
admin.site.register(models.Patient, admin.ModelAdmin)
