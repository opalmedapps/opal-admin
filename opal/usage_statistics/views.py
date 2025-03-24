# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides views for the usage statistics application."""

from io import BytesIO
from types import MappingProxyType
from typing import Final

from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms import Form
from django.http import FileResponse
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from django.views import generic

from opal.core.utils import create_zip, dict_to_csv, dict_to_xlsx
from opal.usage_statistics import forms

from . import constants, queries, utils
from .common import GroupByComponent, GroupReportType

GROUP_STATISTICS_QUERIES: Final = MappingProxyType({
    GroupReportType.SUMMARY_REPORT.name: utils.get_summary_report,
    GroupReportType.RECEIVED_DATA_REPORT.name: utils.get_received_data_report,
    GroupReportType.APP_ACTIVITY_REPORT.name: utils.get_app_activity_report,
})


# EXPORT USAGE STATISTICS PAGES


class SuperUserPermissionsFormViewMixin(UserPassesTestMixin, generic.FormView[Form]):
    """`FormView` mixin that ensures the request is coming from a user with a `superuser` permissions."""

    def test_func(self) -> bool:
        """
        Check if the request is coming from `superuser`.

        The request is rejected for non-superusers.

        Returns:
            `True` if the request is sent by superuser. `False` otherwise.
        """
        return self.request.user.is_superuser


class DownloadFormMixin(generic.FormView[Form]):
    """`FormView` mixin that handles the downloading process of the requesting data in CSV or XLSX format."""

    data: utils.ReportData = {}

    def process_download(self) -> HttpResponseBadRequest | FileResponse:
        """
        Handle a valid form for downloading data in CSV or XLSX format.

        Returns:
            streaming HTTP response containing the data in CSV or XLSX format.
        """
        download_button_handlers = [
            (constants.DOWNLOAD_CSV_BUTTON_NAME, self.download_csv),
            (constants.DOWNLOAD_XLSX_BUTTON_NAME, self.download_xlsx),
        ]

        for button_name, button_handler in download_button_handlers:
            if button_name in self.request.POST:
                return button_handler()

        return HttpResponseBadRequest(_('No valid download option selected.'))

    def download_csv(self) -> FileResponse:
        """
        Generate and return the requesting data in a CSV file.

        Returns:
            streaming HTTP response containing a ZIP file with the requested data in a CSV format.
        """
        csv_files = {}

        for name, data in self.data.items():
            filename = f'{name}.csv'
            csv_files[filename] = dict_to_csv(data)

        zip_file = create_zip(csv_files)

        return FileResponse(
            BytesIO(zip_file),
            as_attachment=True,
            content_type='application/zip',
        )

    def download_xlsx(self) -> FileResponse:
        """
        Generate and return the requesting data in an XLSX file.

        Returns:
            streaming HTTP response containing the requested data in an XLSX format.
        """
        xlsx_file = dict_to_xlsx(self.data)

        return FileResponse(
            BytesIO(xlsx_file),
            as_attachment=True,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )


class GroupUsageStatisticsView(SuperUserPermissionsFormViewMixin, DownloadFormMixin):
    """View for handling group usage statistics requests."""

    form_class = forms.GroupUsageStatisticsForm
    template_name = 'usage_statistics/reports/export_form.html'

    # Note: HttpResponse and FileResponse share the same superclass (HttpResponseBase).
    # See: https://github.com/typeddjango/django-stubs/issues/720
    def form_valid(self, form: Form) -> HttpResponse | FileResponse:  # type: ignore[override]
        """
        Handle a valid group usage statistics form.

        Args:
            form: the valid group usage statistics form.

        Returns:
            streaming HTTP response containing the data in CSV or XLSX format.
        """
        report_type = form.cleaned_data['report_type']
        group_report_query = GROUP_STATISTICS_QUERIES[report_type]
        self.data = group_report_query(
            form.cleaned_data['start_date'],
            form.cleaned_data['end_date'],
            GroupByComponent[form.cleaned_data['group_by']],
        )
        return self.process_download()


class IndividualUsageStatisticsView(SuperUserPermissionsFormViewMixin, DownloadFormMixin):
    """View for handling individual usage statistics requests."""

    form_class = forms.IndividualUsageStatisticsForm
    template_name = 'usage_statistics/reports/export_form.html'

    # Note: HttpResponse and FileResponse share the same superclass (HttpResponseBase).
    # See: https://github.com/typeddjango/django-stubs/issues/720
    def form_valid(self, form: Form) -> HttpResponse | FileResponse:  # type: ignore[override]
        """
        Handle a valid individual usage statistics form.

        Args:
            form: the valid individual usage statistics form.

        Returns:
            streaming HTTP response containing the data in CSV or XLSX format.
        """
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        self.data = {
            'labs_summary_per_patient': queries.fetch_labs_summary_per_patient(start_date, end_date),
            'logins_summary_per_user': queries.fetch_logins_summary_per_user(start_date, end_date),
            'patient_demographic_diagnosis_summary': queries.fetch_patient_demographic_diagnosis_summary(
                start_date,
                end_date,
            ),
        }
        return self.process_download()
