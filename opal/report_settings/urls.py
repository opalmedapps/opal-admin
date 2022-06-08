"""
URL configuration for report settings.

Provides URLs for the API and any additional paths for regular views.
"""
from django.urls import path

from . import views

app_name = 'report-settings'

urlpatterns = [
    # Web pages
    path(
        'template/update/<slug:slug>',
        views.ReportTemplateCreateUpdateView.as_view(),
        name='template-update',
    ),
]
