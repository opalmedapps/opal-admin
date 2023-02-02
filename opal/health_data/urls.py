"""
URL configuration for health-data.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'health_data'

urlpatterns = [
    path(
        '<int:id>/quantity-samples/',
        views.HealthDataView.as_view(),
        name='health-data-ui',
    ),
]
