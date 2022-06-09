"""URL configuration for the report settings API endpoints."""
from django.urls import path

from opal.report_settings.api.views import QuestionnairesReportCreateAPIView

urlpatterns = [
    # Questionnaire report generation endpoint
    path('questionnaires', QuestionnairesReportCreateAPIView.as_view(), name='questionnaires'),
]
