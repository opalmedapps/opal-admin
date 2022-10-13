"""This module provides views for questionnaire settings."""
import logging
from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic.base import TemplateView

import pandas as pd

from .backend import get_all_questionnaire, get_questionnaire_detail, get_tempC, make_tempC
from .models import ExportReportPermission


# QUESTIONNAIRES INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the questionnaires app."""

    template_name = 'questionnaires/index.html'


# EXPORT REPORTS LIST QUESTIONNAIRES
class ExportReportListTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the list of available questionnaires."""

    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    template_name = 'questionnaires/export_reports/exportreports-list.html'

    def get_context_data(self, **kwargs: Any) -> Any:
        """Override class method and append questionnaire list to context.

        Args:
            kwargs: any number of key word arguments.

        Returns:
            dict containing questionnaire list.
        """
        context = super().get_context_data(**kwargs)
        context['questionnaire_list'] = get_all_questionnaire()
        return context


# EXPORT REPORTS QUERY SELECTED QUESTIONNAIRE
class ExportReportQueryTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for selecting query parameters."""

    template_name = 'questionnaires/export_reports/exportreports-query.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)

    @method_decorator(require_http_methods(['POST']))
    def post(self, request: Any) -> Any:
        """Override class method and fetch query parameters for the requested questionnaire.

        Args:
            request: post request data.

        Returns:
            template rendered with updated context or HttpError
        """
        context = self.get_context_data()
        context.update({'title': 'questionnaire detail'})

        qid = request.POST['questionnaireid']
        if qid is not None:
            questionnaire_detail = get_questionnaire_detail(qid)
            context.update(questionnaire_detail)
        else:
            self.logger.error('Request questionnaire not found.')
            return HttpResponse(status=404)  # noqa: WPS432
        return super(TemplateView, self).render_to_response(context)  # noqa: WPS608, WPS613


# EXPORT REPORTS VIEW REPORT
class ExportReportViewReportTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the selected report."""

    template_name = 'questionnaires/export_reports/exportreports-viewreport.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)

    @method_decorator(require_http_methods(['POST']))
    def post(self, request: Any) -> Any:
        """Override class method and fetch report for the requested questionnaire.

        Args:
            request: post request data.

        Returns:
            template rendered with updated context.

        """
        context = self.get_context_data()
        context.update({'title': 'export questionnaire'})
        complete_params_check = make_tempC(request.POST)  # create temporary table for requested questionnaire data

        if not complete_params_check:  # fail with 400 error if query parameters are incomplete
            self.logger.error('Server received incomplete query parameters.')
            return HttpResponse(status=400)  # noqa: WPS432

        report = get_tempC()  # after verifying parameters were complete, retrieve the prepared data

        report_df = pd.DataFrame(report)  # use pandas to convert raw data to html format
        report_df = report_df.to_html(index=False)
        report_df = report_df.replace('<table border="1" class="dataframe">', '<table class="table" id="data_table">')
        report_df = report_df.replace('text-align: right', 'text-align: left')

        context.update({'reporthtml': report_df})  # update context with report results
        context.update({'questionnaireID': request.POST.get('questionnaireid')})

        return super(TemplateView, self).render_to_response(context)  # noqa: WPS608, WPS613
