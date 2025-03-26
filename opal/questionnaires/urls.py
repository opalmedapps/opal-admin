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
        'reports/downloadcsv/',
        views.QuestionnaireReportDownloadCSVTemplateView.as_view(),
        name='reports-downloadcsv',
    ),
    path(
        'reports/downloadxlsx/',
        views.QuestionnaireReportDownloadXLSXTemplateView.as_view(),
        name='reports-downloadxlsx',
    ),
]
