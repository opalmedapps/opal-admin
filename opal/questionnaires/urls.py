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
        'exportreports-list/',
        views.ExportReportListTemplateView.as_view(),
        name='exportreports-list',
    ),
    path(
        'exportreports-query/',
        views.ExportReportQueryTemplateView.as_view(),
        name='exportreports-query',
    ),
]
