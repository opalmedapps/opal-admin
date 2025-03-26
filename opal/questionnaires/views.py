"""This module provides views for questionnaire settings."""
import datetime
import logging
import os
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.views.generic.base import TemplateView

import django_tables2 as tables
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
    http_method_names = ['post']

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


# REPORT TABLE (DjangoTables2)
class ReportTable(tables.Table):
    """Enable rendering of report data with django table2."""

    patientId = tables.Column()
    questionId = tables.Column()
    question = tables.Column()
    Answer = tables.Column()
    creationDate = tables.Column()
    lastUpdated = tables.Column()


# EXPORT REPORTS VIEW REPORT
class ExportReportViewReportTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the selected report."""

    template_name = 'questionnaires/export_reports/exportreports-viewreport.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

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

        report_table = ReportTable(report, orderable=False)  # orderable set false for now to avoid queryset errors
        context.update({'questionnaireID': request.POST.get('questionnaireid')})
        context.update({'reporttable': report_table})
        return super(TemplateView, self).render_to_response(context)  # noqa: WPS608, WPS613


# EXPORT REPORTS VIEW REPORT (Downloaded csv)
class ExportReportDownloadCSVTemplateView(PermissionRequiredMixin, TemplateView):
    """This view returns the same page after downloading the csv to client side."""

    template_name = 'questionnaires/export_reports/exportreports-viewreport.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: Any) -> Any:  # noqa: WPS210
        """Grab existing backend report and convert to csv.

        This code first generates the desired csv by writing it to media folder within
        the questionnaires app.
        After this, that file is served to the clientside with Openfile functionality.

        Args:
            request: post request data.

        Returns:
            original template

        """
        qid = request.POST.get('questionnaireid')
        path = os.path.join(settings.MEDIA_ROOT, 'questionnaire-files')
        datesuffix = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f'questionnaire-{qid}-{datesuffix}.csv'
        filename_long = smart_str(f'{path}/{filename}')
        report_dict = get_tempC()
        df = pd.DataFrame.from_dict(report_dict)

        df.to_csv(filename_long, index=False, header=True)
        return HttpResponse(
            open(filename_long, 'rb').read(),  # noqa: WPS515
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename = {filename}'},
        )


# EXPORT REPORTS VIEW REPORT (Downloaded xlsx)
class ExportReportDownloadXLSXTemplateView(PermissionRequiredMixin, TemplateView):
    """This view returns the same page after downloading the xlsx to client side."""

    template_name = 'questionnaires/export_reports/exportreports-viewreport.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: Any) -> Any:  # noqa: WPS210
        """Grab existing backend report and convert to xlsx.

        This code first generates the desired xlsx by writing it to media folder within
        the questionnaires app.
        After this, that file is served to the clientside with Openfile functionality.

        Args:
            request: post request data.

        Returns:
            template rendered with updated context.

        """
        qid = request.POST.get('questionnaireid')
        tabs = request.POST.get('tabs')

        path = os.path.join(settings.MEDIA_ROOT, 'questionnaire-files')
        datesuffix = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f'questionnaire-{qid}-{datesuffix}.xlsx'
        filename_long = smart_str(f'{path}/{filename}')
        report_dict = get_tempC()
        df = pd.DataFrame.from_dict(report_dict)

        if tabs == 'patients':
            pids = df['patientId'].unique()
            pids.sort()
            with pd.ExcelWriter(filename_long) as writer:  # noqa: WPS440
                for pat in pids:
                    patient_rows = df.loc[df['patientId'] == pat]
                    patient_rows = patient_rows.sort_values(['lastUpdated', 'questionId'], ascending=[True, True])
                    patient_rows.to_excel(writer, sheet_name=f'patient-{pat}', index=False, header=True)
        elif tabs == 'questions':
            qids = df['questionId'].unique()
            qids.sort()
            with pd.ExcelWriter(filename_long) as writer:  # noqa: WPS440
                for ques in qids:
                    patient_rows = df.loc[df['questionId'] == ques]
                    patient_rows = patient_rows.sort_values(['lastUpdated', 'patientId'], ascending=[True, True])
                    patient_rows.to_excel(writer, sheet_name=f'questionId-{ques}', index=False, header=True)
        else:
            df.to_excel(filename_long, sheet_name='Sheet1', index=False, header=True)

        return HttpResponse(
            open(filename_long, 'rb').read(),  # noqa: WPS515
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename = {filename}'},
        )
