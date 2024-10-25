"""
URL configuration for usage statistics.

Provides URLs for regular views.
"""

from django.urls import path

from . import views

app_name = 'usage-statistics'

urlpatterns = [
    # Usage statistics pages
    path(
        'export/',
        views.UsageStatisticsExportTemplateView.as_view(),
        name='data-export',
    ),
]
