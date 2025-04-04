# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
URL configuration for health-data.

Provides URLs for regular views.
"""

from django.urls import path

from . import views

app_name = 'health_data'

urlpatterns = [
    path(
        '<uuid:uuid>/quantity-samples/',
        views.HealthDataView.as_view(),
        name='health-data-ui',
    ),
]
