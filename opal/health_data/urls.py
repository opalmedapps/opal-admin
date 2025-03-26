"""
URL configuration for health-data.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'health_data'

urlpatterns = [
    path(
        '<int:id>/health-data/quantity-samples/',
        views.HealthDataView.as_view(),
        name='health-data',
    ),
]
