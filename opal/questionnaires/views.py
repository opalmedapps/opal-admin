"""This module provides views for questionnaire settings."""
import datetime
import logging
import tempfile
from http import HTTPStatus
from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.views.generic.base import TemplateView

import pandas as pd
from easyaudit.models import RequestEvent

from ..users.models import User
from .backend import get_all_questionnaire, get_questionnaire_detail, get_temp_table, make_temp_tables
from .models import ExportReportPermission
from .tables import ReportTable

language_map = {'fr': 1, 'en': 2}  # All queries assume the integer representation of opal languages


# QUESTIONNAIRES INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the questionnaires app."""

    template_name = 'questionnaires/index.html'


# EXPORT REPORTS LIST QUESTIONNAIRES
class QuestionnaireReportListTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the list of available questionnaires."""

    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    template_name = 'questionnaires/export_reports/reports-list.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Override class method and append questionnaire list to context.

        Args:
            kwargs: any number of key word arguments.

        Returns:
            dict containing questionnaire list.
        """
        context = super().get_context_data(**kwargs)
        requestor = User.objects.get(username=context['username'])
        context['questionnaire_list'] = get_all_questionnaire(language_map[requestor.language])
        return context


# EXPORT REPORTS QUERY SELECTED QUESTIONNAIRE
class QuestionnaireReportFilterTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for selecting query parameters."""

    template_name = 'questionnaires/export_reports/reports-filter.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:
        """Override class method and fetch query parameters for the requested questionnaire.

        Args:
            request: post request data.

        Returns:
            template rendered with updated context or HttpError
        """
        context = self.get_context_data()
        requestor = User.objects.get(username=request.user)

        if 'questionnaireid' in request.POST.keys():
            try:
                qid = int(request.POST['questionnaireid'])
            except ValueError:
                self.logger.error('Invalid request format for questionnaireid')
                return HttpResponse(status=HTTPStatus.BAD_REQUEST)
            questionnaire_detail = get_questionnaire_detail(int(qid), language_map[requestor.language])
            context.update(questionnaire_detail)
            # Also update auditing service with request details
            request_event = RequestEvent.objects.filter(
                url=request.path,
            ).order_by('-datetime').first()
            request_event.query_string = f'questionnaireid: {qid}'
            request_event.save()
            return self.render_to_response(context)
        self.logger.error('Missing post key: questionnaireid')
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)


# EXPORT REPORTS VIEW REPORT
class QuestionnaireReportDetailTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the selected report."""

    template_name = 'questionnaires/export_reports/reports-detail.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:  # noqa: WPS210
        """Override class method and fetch report for the requested questionnaire.

        Args:
            request: post request data.

        Returns:
            template rendered with updated context.

        """
        context = self.get_context_data()
        context.update({'title': 'export questionnaire'})

        requestor = User.objects.get(username=request.user)

        #  make_temp_tables() creates a temporary table in the QuestionnaireDB containing the desired data report
        #  the function returns a boolean indicating if the table could be succesfully created given the query params
        complete_params_check = make_temp_tables(request.POST, language_map[requestor.language])

        if not complete_params_check:  # fail with 400 error if query parameters are incomplete
            self.logger.error('Server received incomplete query parameters.')
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        report = get_temp_table()  # after verifying parameters were complete, retrieve the prepared data

        report_table = ReportTable(report)
        context.update(
            {
                'questionnaireID': request.POST.get('questionnaireid'),
                'reporttable': report_table,
                'questionnaireName': request.POST.get('questionnairename'),
                'start': request.POST.get('start'),
                'end': request.POST.get('end'),
            },
        )

        # Also update auditing service with request details
        request_event = RequestEvent.objects.filter(
            url=request.path,
        ).order_by('-datetime').first()
        request_event.query_string = {
            'questionnaireid: {0}'.format(request.POST.get('questionnaireid')),
            'startdate: {0}'.format(request.POST.get('start')),
            'enddate: {0}'.format(request.POST.get('end')),
            'patientIdFilter: {0}'.format(request.POST.getlist('patientIDs')),
            'questionIdFilter: {0}'.format(request.POST.getlist('questionIDs')),
        }
        request_event.save()

        return self.render_to_response(context)


# EXPORT REPORTS VIEW REPORT (Downloaded csv)
class QuestionnaireReportDownloadCSVTemplateView(PermissionRequiredMixin, TemplateView):
    """This view returns the same page after downloading the csv to client side."""

    template_name = 'questionnaires/export_reports/reports-detail.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:  # noqa: WPS210
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
        datesuffix = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f'questionnaire-{qid}-{datesuffix}.csv'
        report_dict = get_temp_table()
        df = pd.DataFrame.from_dict(report_dict)

        with tempfile.NamedTemporaryFile() as temp_file:
            df.to_csv(temp_file.name, index=False, header=True)
            return HttpResponse(
                temp_file.read(),
                content_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename = {filename}'},
            )


# EXPORT REPORTS VIEW REPORT (Downloaded xlsx)
class QuestionnaireReportDownloadXLSXTemplateView(PermissionRequiredMixin, TemplateView):
    """This view returns the same page after downloading the xlsx to client side."""

    template_name = 'questionnaires/export_reports/reports-detail.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:  # noqa: WPS210
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
        datesuffix = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f'questionnaire-{qid}-{datesuffix}.xlsx'
        report_dict = get_temp_table()
        df = pd.DataFrame.from_dict(report_dict)

        with tempfile.NamedTemporaryFile(suffix='.xlsx') as temp_file:
            if tabs == 'none':
                # return everything as one xlsx sheet, no dellineation by sheet
                df.to_excel(temp_file.name, sheet_name='Sheet1', index=False, header=True)
            else:
                # sort by patient or question id
                column_name = 'patient_id' if tabs == 'patients' else 'question_id'
                sheet_prefix = 'patient' if tabs == 'patients' else 'question_id'
                sort_rows_column = 'question_id' if tabs == 'patients' else 'patient_id'

                ids = df[column_name].unique()
                ids.sort()

                with pd.ExcelWriter(temp_file.name) as writer:
                    for current_id in ids:
                        patient_rows = df.loc[df[column_name] == current_id]
                        patient_rows = patient_rows.sort_values(
                            by=['last_updated', sort_rows_column],
                            ascending=[True, True],
                        )
                        patient_rows.to_excel(
                            writer,
                            sheet_name=f'{sheet_prefix}-{current_id}',
                            index=False,
                            header=True,
                        )

            file_content = temp_file.read()

        return HttpResponse(
            file_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename = {filename}'},
        )
