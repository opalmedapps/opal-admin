"""This module provides views for the report settings."""

from django.urls import reverse_lazy
from django.views.generic import UpdateView

from opal.report_settings.forms import ReportTemplateForm

from .models import ReportTemplate


class ReportTemplateCreateUpdateView(UpdateView):
    """
    This `UpdateView` displays a form for creating and updating a report object.

    It redisplays the form with validation errors (if there are any) and saves the report object.

    The view updates only the first element of the model objects since there is only one report template.
    """

    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'report_settings/template/template_form.html'
    success_url = reverse_lazy('report-settings:template-update')
