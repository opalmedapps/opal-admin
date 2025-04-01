# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing business logic for generating charts using plotly library."""

import logging
from types import MappingProxyType
from typing import Final, NamedTuple

import pandas as pd
from plotly import express as px


class ChartData(NamedTuple):
    """
    Typed `NamedTuple` that describes data fields needed for generating a chart.

    Attributes:
        title: the title that is shown on top of the chart
        label_x: label that is shown for the x axis
        label_y: label that is shown for the y axis
        label_legend: caption that is shown in the legend section (the legend name)
        data: DataFrame that contain records required to build the chart
    """

    title: str
    label_x: str
    label_y: str
    label_legend: str
    data: pd.DataFrame


CHART_LAYOUT: Final = MappingProxyType({
    'hovermode': 'x unified',
    'dragmode': False,
    'plot_bgcolor': '#ffffff',
    'paper_bgcolor': '#ffffff',
    'yaxis': {
        'gridcolor': '#f2f2f2',
        'rangemode': 'tozero',
    },
})

LOGGER = logging.getLogger(__name__)


class ChartService:
    """Service that provides functionality for generating plotly charts in HTML format."""

    def generate_error_bar_chart(
        self,
        chart_data: ChartData,
        label_error_min: str = 'min',
        label_error_max: str = 'max',
    ) -> str | None:
        """
        Generate a plotly error bar chart.

        The DataFrame should contain x, error_max, error_min, and legend records.

        Args:
            chart_data: chart data needed to generate error bar chart
            label_error_min: label for the hover legend minimum error bar
            label_error_max: label for the hover legend maximum error bar

        Returns:
            HTML string representation of the plot
        """
        if chart_data.data.empty:
            return None

        if not set({'x', 'error_max', 'error_min', 'legend'}).issubset(chart_data.data.columns):
            LOGGER.error(
                'An error occurred in ChartService::generate_error_bar_chart(chart_data: ChartData):\n'
                + 'chart_data.data should contain the following columns: x, error_max, error_min, legend\n'
                + f'The columns received: {chart_data.data.columns}\n\n',
            )
            return None

        chart_data.data['error_diff'] = chart_data.data['error_max'] - chart_data.data['error_min']
        figure = px.scatter(
            chart_data.data,
            x='x',
            y='error_max',
            title=chart_data.title,
            color='legend',
            labels={
                'x': chart_data.label_x,
                'error_max': chart_data.label_y,
                'legend': chart_data.label_legend,
            },
            error_y=[0] * len(chart_data.data['error_max']),
            error_y_minus='error_diff',
            hover_data={
                'error_min': False,
                'error_max': False,
                'error_diff': False,
                'x': False,
                label_error_max: chart_data.data['error_max'],
                label_error_min: chart_data.data['error_min'],
                'legend': True,
            },
        )

        figure.update_layout(CHART_LAYOUT)

        return figure.to_html()  # type: ignore[no-any-return]

    def generate_line_chart(
        self,
        chart_data: ChartData,
    ) -> str | None:
        """
        Generate a plotly line chart.

        The DataFrame should contain x, value, and legend records.

        Args:
            chart_data: chart data needed to generate line chart

        Returns:
            HTML string representation of the plot
        """
        if chart_data.data.empty:
            return None

        if not set({'x', 'y', 'legend'}).issubset(chart_data.data.columns):
            LOGGER.error(
                'An error occurred in ChartService::generate_line_chart(chart_data: ChartData):\n'
                + 'chart_data.data should contain the following columns: x, y, legend\n'
                + f'The columns received: {chart_data.data.columns}\n\n',
            )
            return None

        #  Plotly chart customization: https://plotly.com/python/line-charts/
        figure = px.line(
            chart_data.data,
            x='x',
            y='y',
            title=chart_data.title,
            color='legend',
            markers=True,
            labels={
                'x': chart_data.label_x,
                'y': chart_data.label_y,
                'legend': chart_data.label_legend,
            },
            hover_data=['y', 'legend'],
        )

        figure.update_layout(CHART_LAYOUT)

        return figure.to_html()  # type: ignore[no-any-return]
