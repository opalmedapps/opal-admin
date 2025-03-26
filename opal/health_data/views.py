"""This module provides views for any health-data related functionality."""
from typing import Any, Dict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import QuerySet
from django.views import generic

from ..patients.models import Patient
from .models import QuantitySample


class HealthDataView(generic.ListView, PermissionRequiredMixin):
    """A page for visualizing a patient's health data samples.

    Note: This page is currently not accessible from the Django UI as it is meant to be directly linked to.
          The `id` URL argument refers to the pk/id of the patient of interest.

    """

    model = QuantitySample
    template_name = 'health_data_display.html'
    permission_required = ('health_data.view_quantitysample')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Update the context with patient identifiers and wearables plot HTML strings.

        Args:
            kwargs: the context data

        Returns:
            Dict[str, Any]
        """
        print('HERE')
        context = super().get_context_data(**kwargs)
        context.update(
            {'patient': Patient.objects.get(id=self.kwargs['id'])},
        )
        return context

    def get_queryset(self) -> QuerySet[QuantitySample]:
        """Filter QuantitySample data according to kwarg patient id.

        Returns:
            QuerySet[QuantitySample]
        """
        return QuantitySample.objects.filter(
            patient=Patient.objects.get(id=self.kwargs['id']),
        )
