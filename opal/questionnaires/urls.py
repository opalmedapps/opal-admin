"""
URL configuration for questionnaires.

Provides URLs for regular views.
"""
from django.conf import settings
from django.conf.urls.static import static
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
    path(
        'exportreports-viewreport/',
        views.ExportReportViewReportTemplateView.as_view(),
        name='exportreports-viewreport',
    ),
    path(
        'exportreports-downloadcsv/',
        views.ExportReportDownloadCSVTemplateView.as_view(),
        name='exportreports-downloadcsv',
    ),
    path(
        'exportreports-downloadxlsx/',
        views.ExportReportDownloadXLSXTemplateView.as_view(),
        name='exportreports-downloadxlsx',
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
