"""This module provides views for questionnaire settings."""
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.base import RedirectView, TemplateView

from .models import ExportReportPerm


# QUESTIONNAIRES INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the questionnaires app."""

    template_name = 'questionnaires/index.html'


# EXPORT REPORTS
class ExportReportTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for the export reports page."""

    model = ExportReportPerm
    permission_required = ('questionnaires.view_report')
    template_name = 'questionnaires/export_reports/exportreports.html'


# LAUNCH REPORT
class ExportReportLaunch(PermissionRequiredMixin, RedirectView):
    """This view launches the stand alone reporting tool (must be running already)."""

    model = ExportReportPerm
    permission_required = ('questionnaires.launch_report')
    url = settings.EPRO_DATA_EXTRACTIONS_URL
