"""
URL configuration for questionnaires.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'questionnaires'

urlpatterns = [
    # Questionnaires placeholder index page for future functionality
    path('', views.IndexTemplateView.as_view(), name='index'),
    # Export Reports
    path(
        'reports/',
        views.QuestionnaireReportDashboardTemplateView.as_view(),
        name='reports',
    ),
    path(
        'reports/list/',
        views.QuestionnaireReportListTemplateView.as_view(),
        name='reports-list',
    ),
    path(
        'reports/filter/',
        views.QuestionnaireReportFilterTemplateView.as_view(),
        name='reports-filter',
    ),
    path(
        'reports/detail/',
        views.QuestionnaireReportDetailTemplateView.as_view(),
        name='reports-detail',
    ),
    path(
        'reports/download-csv/',
        views.QuestionnaireReportDownloadCSVTemplateView.as_view(),
        name='reports-download-csv',
    ),
    path(
        'reports/download-xlsx/',
        views.QuestionnaireReportDownloadXLSXTemplateView.as_view(),
        name='reports-download-xlsx',
    ),
]
