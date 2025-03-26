"""This module provides views for any health-data related functionality."""
from typing import Any, Dict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import generic

from ..patients.models import Patient
from .models import QuantitySample


class HealthDataView(PermissionRequiredMixin, generic.TemplateView):
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
        context = super().get_context_data(**kwargs)
        context.update(
            {'patient': get_object_or_404(Patient, id=self.kwargs['id'])},
        )
        return context
