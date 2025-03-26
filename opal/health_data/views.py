"""This module provides views for any health-data related functionality."""
from typing import Any, Dict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import generic

import pandas as pd
from plotly import graph_objects as go

from ..patients.models import Patient
from .models import QuantitySample, QuantitySampleType


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
        patient = get_object_or_404(Patient, id=self.kwargs['id'])
        x_axis = str(_('Date'))
        context.update(
            {
                'patient': patient,
                'bm_graph': self._generate_plot(
                    title=str(_('Body Mass')),
                    xlab=x_axis,
                    ylab=str(QuantitySampleType.BODY_MASS.label),
                    data=QuantitySample.objects.filter(
                        patient=patient,
                        type__in=[QuantitySampleType.BODY_MASS],
                    ),
                ),
                'bt_graph': self._generate_plot(
                    title=str(_('Body Temperature')),
                    xlab=x_axis,
                    ylab=str(QuantitySampleType.BODY_TEMPERATURE.label),
                    data=QuantitySample.objects.filter(
                        patient=patient,
                        type__in=[QuantitySampleType.BODY_TEMPERATURE],
                    ),
                ),
                'hr_graph': self._generate_plot(
                    title=str(_('Heart Rate')),
                    xlab=x_axis,
                    ylab=str(QuantitySampleType.HEART_RATE.label),
                    data=QuantitySample.objects.filter(
                        patient=patient,
                        type__in=[QuantitySampleType.HEART_RATE],
                    ),
                ),
                'hrv_graph': self._generate_plot(
                    title=str(_('Heart Rate Variability')),
                    xlab=x_axis,
                    ylab=str(QuantitySampleType.HEART_RATE_VARIABILITY.label),
                    data=QuantitySample.objects.filter(
                        patient=patient,
                        type__in=[QuantitySampleType.HEART_RATE_VARIABILITY],
                    ),
                ),
                'os_graph': self._generate_plot(
                    title=str(_('Oxygen Saturation')),
                    xlab=x_axis,
                    ylab=str(QuantitySampleType.OXYGEN_SATURATION),
                    data=QuantitySample.objects.filter(
                        patient=patient,
                        type__in=[QuantitySampleType.OXYGEN_SATURATION],
                    ),
                ),
            },
        )
        return context

    def _generate_plot(self, title: str, xlab: str, ylab: str, data: QuerySet) -> Any:  # noqa: WPS210
        """Generate a plotly chart for the given sample type.

        Args:
            title: Plot title
            xlab: x axis label
            ylab: y axis label
            data: QuantitySample queryset

        Returns:
            Html string representation of the plot
        """
        if data:
            df = pd.DataFrame(list(data.values()))
            x_data = df.start_date.sort_values(ascending=True)  # All lines in a given plot to be shown on same x axis
            devices = df.device.unique()  # One set of values for each unique device identifier

            layout = go.Layout(
                title=title,
                xaxis={'title': xlab},
                yaxis={'title': ylab},
                legend={'title': 'Device'},
            )

            # Graph objects are instances of the automatically generated hierarchy of python classes in Plotly
            #   Their benefit over the Plotly express functions is the access to render or them in various formats
            #   for example in our case here where we want to export the plot as html
            #   https://plotly.com/python/graph-objects/
            fig = go.Figure(layout=layout)

            # We will have one line for each unique device
            for device in devices:
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=list(df.loc[df['device'] == device]['value']),
                        mode='lines+markers',
                        name=device,
                    ),
                )
            return fig.to_html()
        return ''
