"""This module provides views for any health-data related functionality."""
from typing import Any, Dict, Optional

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from django.views import generic

import pandas as pd
from plotly import express as px

from ..patients.models import Patient
from .models import QuantitySample, QuantitySampleType


class HealthDataView(PermissionRequiredMixin, generic.TemplateView):
    """A page for visualizing a patient's health data samples.

    Note: This page is currently not accessible from the Django UI as it is meant to be directly linked to.
          The keyword argument in the URL refers to the uuid of the patient of interest.

    """

    model = QuantitySample
    permission_required = ('health_data.view_quantitysample')
    http_method_names = ['get', 'head', 'options', 'trace']

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Update the context with patient identifiers and wearables plot HTML strings.

        Args:
            kwargs: the context data

        Returns:
            Dict[str, Any]
        """
        context = super().get_context_data(**kwargs)
        patient = get_object_or_404(Patient, uuid=self.kwargs['uuid'])

        graphs = {}
        for sample_type in QuantitySampleType:
            graphs[sample_type.label.split(' (')[0]] = self._generate_plot(
                title=str(sample_type.label),
                label_x=gettext('Date'),
                label_y=str(sample_type.label),
                data=QuantitySample.objects.order_by('start_date').filter(
                    patient=patient,
                    type=sample_type,
                ),
            )

        context.update(
            {
                'patient': patient,
                'graphs': graphs,
            },
        )
        return context

    def get_template_names(self) -> list[str]:
        """Return a list of template names to be used for the request based on the request type.

        Provide partial HTML for the wearables data charts if receive AJAX GET request.
        Otherwise return the whole page.

        See `TemplateResponseMixin` for more details.

        Returns:
            List of template names
        """
        if (
            self.request.method == 'GET'
            and 'x-orms-wearablecharts' in self.request.headers
            and self.request.headers.get('x-orms-wearablecharts') == 'True'
        ):
            return ['chart_display.html']

        return ['index.html']

    def _generate_plot(self, title: str, label_x: str, label_y: str, data: QuerySet[QuantitySample]) -> Optional[str]:
        """Generate a plotly chart for the given sample type.

        Args:
            title: Plot title
            label_x: x axis label
            label_y: y axis label
            data: QuantitySample queryset

        Returns:
            Html string representation of the plot
        """
        if data:
            df = pd.DataFrame(data.values('start_date', 'value', 'device'))

            #  Plotly chart customization: https://plotly.com/python/line-charts/
            figure = px.line(
                df,
                x='start_date',
                y='value',
                title=title,
                color='device',
                markers=True,
                labels={
                    'start_date': label_x,
                    'value': label_y,
                    'device': gettext('Device'),
                },
                hover_data=['value', 'device'],
            )

            figure.update_layout({
                'hovermode': 'x unified',
                'dragmode': False,
                'plot_bgcolor': '#ffffff',
                'paper_bgcolor': '#ffffff',
                'yaxis': {
                    'gridcolor': '#f2f2f2',
                    'rangemode': 'tozero',
                },
            })

            return figure.to_html()  # type: ignore[no-any-return]
        return None
