# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides views for questionnaire settings."""

import logging
from http import HTTPStatus
from io import BytesIO, StringIO
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.views.generic.base import TemplateView

import pandas as pd
import structlog
from django_structlog import signals

from .models import QuestionnaireProfile
from .queries import get_all_questionnaires, get_questionnaire_detail, get_temp_table, make_temp_tables
from .tables import ReportTable

if TYPE_CHECKING:
    from ..users.models import User


@receiver(signals.bind_extra_request_metadata)
def bind_questionnaire(request: HttpRequest, logger: logging.Logger, **kwargs: Any) -> None:
    """
    Binds the questionnaire to the request context to know which questionnaire is being exported.

    Args:
        request: The request
        logger: The logger
        kwargs: additional keyword arguments
    """
    questionnaire_id = request.POST.get('questionnaireid')
    if questionnaire_id:
        structlog.contextvars.bind_contextvars(questionnaire_id=questionnaire_id)

    questionnaire_name = request.POST.get('questionnairename')
    if questionnaire_name:
        structlog.contextvars.bind_contextvars(questionnaire_name=questionnaire_name)


# All queries assume the integer representation of opal languages
LANGUAGE_MAP = MappingProxyType({'fr': 1, 'en': 2})


# QUESTIONNAIRES INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the questionnaires app."""

    template_name = 'questionnaires/index.html'


# EXPORT REPORTS USER DASHBOARD
class QuestionnaireReportDashboardTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing a user's saved questionnaires dashboard."""

    permission_required = 'questionnaires.export_report'
    template_name = 'questionnaires/export_reports/reports-dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Override class method and append user's followed questionnaires.

        Args:
            kwargs: any number of key word arguments.

        Returns:
            dict containing questionnaire list.
        """
        context = super().get_context_data(**kwargs)
        requestor: User = self.request.user  # type: ignore[assignment]
        # Update context with this user's questionnaire profile, create new one if not found
        questionnaires_following, _ = QuestionnaireProfile.objects.get_or_create(
            user=requestor,
        )

        context['questionnaires_following'] = questionnaires_following.questionnaire_list

        return context


# EXPORT REPORTS LIST QUESTIONNAIRES
class QuestionnaireReportListTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the list of available questionnaires."""

    permission_required = 'questionnaires.export_report'
    template_name = 'questionnaires/export_reports/reports-list.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Override class method and append questionnaire list to context.

        Args:
            kwargs: any number of key word arguments.

        Returns:
            dict containing questionnaire list.
        """
        context = super().get_context_data(**kwargs)
        # due to the LoginRequiredMiddleware we know that this can only be an authenticated user (not AnonymousUser)
        requestor: User = self.request.user  # type: ignore[assignment]
        context['questionnaire_list'] = get_all_questionnaires(LANGUAGE_MAP[requestor.language])
        return context


# EXPORT REPORTS QUERY SELECTED QUESTIONNAIRE
class QuestionnaireReportFilterTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for selecting query parameters."""

    template_name = 'questionnaires/export_reports/reports-filter.html'
    permission_required = 'questionnaires.export_report'
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Override class method and fetch query parameters for the requested questionnaire.

        Args:
            request: post request data.

        Returns:
            template rendered with updated context or HttpError.
        """
        context = self.get_context_data()
        requestor: User = request.user  # type: ignore[assignment]

        questionnaire_id = request.POST.get('questionnaireid')

        if questionnaire_id:
            try:
                qid = int(questionnaire_id)
            except ValueError:
                self.logger.exception('Invalid request format for questionnaireid')
                return HttpResponse(status=HTTPStatus.BAD_REQUEST)

            context.update(get_questionnaire_detail(qid, LANGUAGE_MAP[requestor.language]))

            # Finally check if this questionnaire is currently being followed
            questionnaires_following = QuestionnaireProfile.objects.get(user=requestor)
            is_following = str(qid) in questionnaires_following.questionnaire_list
            context.update({'following': is_following})

            return self.render_to_response(context)
        self.logger.error('Missing post key: questionnaireid')
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)


# EXPORT REPORTS VIEW REPORT
class QuestionnaireReportDetailTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the selected report."""

    template_name = 'questionnaires/export_reports/reports-detail.html'
    permission_required = 'questionnaires.export_report'
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Override class method and fetch report for the requested questionnaire.

        Args:
            request: post request data.

        Returns:
            template rendered with updated context.

        """
        context = self.get_context_data()
        requestor: User = request.user  # type: ignore[assignment]

        #  make_temp_tables() creates a temporary table in the QuestionnaireDB containing the desired data report
        #  the function returns a boolean indicating if the table could be successfully created given the query params
        complete_params_check = make_temp_tables(request.POST, LANGUAGE_MAP[requestor.language])

        if not complete_params_check:  # fail with 400 error if query parameters are incomplete
            self.logger.error('Server received incomplete query parameters.')
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        # Update questionnaire following list if user selected option
        toggle = 'following' in request.POST

        QuestionnaireProfile.update_questionnaires_following(
            request.POST['questionnaireid'],
            request.POST['questionnairename'],
            requestor,
            toggle,
        )

        # After verifying parameters were complete, retrieve the prepared data
        report = get_temp_table()

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

        return self.render_to_response(context)


# EXPORT REPORTS VIEW REPORT (Downloaded csv)
class QuestionnaireReportDownloadCSVTemplateView(PermissionRequiredMixin, TemplateView):
    """This view returns the same page after downloading the csv to client side."""

    template_name = 'questionnaires/export_reports/reports-detail.html'
    permission_required = 'questionnaires.export_report'
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Grab existing backend report and convert to csv.

        This code first generates the desired csv by writing it to media folder within
        the questionnaires app.
        After this, that file is served to the client side with Openfile functionality.

        Args:
            request: post request data.

        Returns:
            original template.

        """
        qid = request.POST.get('questionnaireid')
        datesuffix = timezone.now().date().isoformat()
        filename = f'questionnaire-{qid}-{datesuffix}.csv'
        df_report = pd.DataFrame.from_records(
            get_temp_table(),
        )

        buffer = StringIO()
        df_report.to_csv(buffer, index=False, header=True)
        return HttpResponse(
            buffer.getvalue(),
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename = {filename}'},
        )


# EXPORT REPORTS VIEW REPORT (Downloaded xlsx)
class QuestionnaireReportDownloadXLSXTemplateView(PermissionRequiredMixin, TemplateView):
    """This view returns the same page after downloading the xlsx to client side."""

    template_name = 'questionnaires/export_reports/reports-detail.html'
    permission_required = 'questionnaires.export_report'
    logger = logging.getLogger(__name__)
    http_method_names = ['post']

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Grab existing backend report and convert to xlsx.

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
        date_suffix = timezone.now().date().isoformat()
        filename = f'questionnaire-{qid}-{date_suffix}.xlsx'
        report_dict = get_temp_table()
        df_report = pd.DataFrame.from_records(report_dict)
        buffer = BytesIO()

        if tabs == 'none' or df_report.empty:
            # If df is empty return an empty download to avoid a potential key error
            df_report.to_excel(buffer, sheet_name='Sheet1', index=False, header=True)
        else:
            # sort by patient or question id
            column_name = 'patient_id' if tabs == 'patients' else 'question_id'
            sheet_prefix = 'patient' if tabs == 'patients' else 'question_id'
            sort_rows_column = 'question_id' if tabs == 'patients' else 'patient_id'
            ids = df_report[column_name].unique()
            ids.sort()
            with pd.ExcelWriter(buffer) as writer:
                for current_id in ids:
                    patient_rows = df_report.loc[df_report[column_name] == current_id]
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

        return HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename = {filename}'},
        )
