"""This module provides views for any health-data related functionality."""

from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import generic

from ..patients.models import Patient
from .models import QuantitySample
from .utils import build_all_quantity_sample_charts


class HealthDataView(PermissionRequiredMixin, generic.TemplateView):
    """A page for visualizing a patient's health data samples.

    Note: This page is currently not accessible from the Django UI as it is meant to be directly linked to.
          The keyword argument in the URL refers to the uuid of the patient of interest.

    """

    model = QuantitySample
    template_name = 'chart_display.html'
    permission_required = ('health_data.view_quantitysample')
    http_method_names = ['get', 'head', 'options', 'trace']

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Update the context with patient identifiers and wearables plot HTML strings.

        Args:
            kwargs: the context data

        Returns:
            the context data
        """
        context = super().get_context_data(**kwargs)
        patient = get_object_or_404(Patient, uuid=self.kwargs['uuid'])
        graphs = build_all_quantity_sample_charts(patient)

        context.update(
            {
                'patient': patient,
                'graphs': graphs,
            },
        )
        return context
