"""This module provides views for questionnaire settings."""
from django.conf import settings
from django.views.generic.base import RedirectView, TemplateView


# QUESTIONNAIRES INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the questionnaires app."""

    template_name = 'questionnaires/index.html'


# EXPORT REPORTS
class ExportReportTemplateView(TemplateView):
    """This `TemplateView` provides a basic rendering for the export reports page."""

    template_name = 'questionnaires/export_reports/exportreports.html'


# LAUNCH REPORT
class ExportReportLaunch(RedirectView):
    """This view launches the stand alone reporting tool (must be running already)."""

    url = settings.EPRO_DATA_EXTRACTIONS_URL
