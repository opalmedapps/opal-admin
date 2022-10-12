"""This module provides views for questionnaire settings."""
from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.views.generic.base import TemplateView

from .backend import get_all_questionnaire, get_questionnaire_detail
from .models import ExportReportPermission


# QUESTIONNAIRES INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the questionnaires app."""

    template_name = 'questionnaires/index.html'


# EXPORT REPORTS LIST QUESTIONNAIRES
class ExportReportListTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for viewing the list of available questionnaires."""

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

    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')
    template_name = 'questionnaires/export_reports/exportreports-list.html'


# EXPORT REPORTS QUERY SELECTED QUESTIONNAIRE
class ExportReportQueryTemplateView(PermissionRequiredMixin, TemplateView):
    """This `TemplateView` provides a basic rendering for selecting query parameters."""

    template_name = 'questionnaires/export_reports/exportreports-query.html'
    model = ExportReportPermission
    permission_required = ('questionnaires.export_report')

    def post(self, request: Any) -> Any:
        """Override class method and fetch details for the requested questionnaire.

        Args:
            request: post request data.

        Returns:
                    template rendered with updated context.

        Raises:
            Http404: on questionnaire not found in QuestionnaireDB.


        """
        context = self.get_context_data()
        if request.method == 'POST':
            print(request.POST)
            context.update({'title': 'questionnaire detail'})

            qid = request.POST['questionnaireid']
            if qid is not None:
                questionnaire_detail = get_questionnaire_detail(qid)
                context.update(questionnaire_detail)
                print(context)
            else:
                raise Http404('Questionnaire does not exist')
            print(context)
            return super(TemplateView, self).render_to_response(context)  # noqa: WPS608, WPS613
