"""
URL configuration for questionnaires.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'questionnaires'

urlpatterns = [
    # Questionnaires index
    path('', views.IndexTemplateView.as_view(), name='index'),
    # Export Reports
    path(
        'exportreports/',
        views.ExportReportTemplateView.as_view(),
        name='exportreports',
    ),
    path(
        'exportreports/launch/',
        views.ExportReportLaunch.as_view(),
        name='exportreports-launch',
    ),
]
