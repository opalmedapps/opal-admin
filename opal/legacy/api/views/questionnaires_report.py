"""Collection of api views used to send questionnaire PDF reports to the source system."""

import base64
import logging
from typing import Any

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils import timezone

from rest_framework import response, status, views
from rest_framework.request import Request

from opal.core.drf_permissions import IsORMSUser
from opal.legacy.utils import generate_questionnaire_report, get_questionnaire_data
from opal.patients.models import Patient
from opal.services.hospital.hospital import SourceSystemReportExportData, SourceSystemService

from ..serializers import QuestionnaireReportRequestSerializer

LOGGER = logging.getLogger(__name__)


class QuestionnairesReportView(views.APIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = (IsORMSUser,)
    serializer_class = QuestionnaireReportRequestSerializer
    source_system = SourceSystemService()

    def post(
        self,
        request: Request,
        *args: Any,
        **kwargs: Any,
    ) -> response.Response:
        """
        Generate questionnaire PDF report and submit to the source system.

        Args:
            request: HTTP request that initiates report generation
            args: varied amount of non-keyword arguments
            kwargs: varied amount of keyword arguments

        Returns:
            HTTP `Response` with results of report generation
        """
        serializer = QuestionnaireReportRequestSerializer(data=request.data)
        # Validate received data. Return a 400 response if the data was invalid.
        serializer.is_valid(raise_exception=True)

        try:
            patient = Patient.objects.get_patient_by_site_mrn_list(
                [
                    {
                        'site': {'acronym': serializer.validated_data.get('site')},
                        'mrn': serializer.validated_data.get('mrn'),
                    },
                ],
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return self._create_error_response(
                'Could not find `Patient` record with the provided MRN and site acronym.',
            )

        # Generate questionnaire report
        pdf_report = generate_questionnaire_report(patient, get_questionnaire_data(patient))
        encoded_report = base64.b64encode(pdf_report).decode('utf-8')

        # The `ReportService` does not return error messages.
        # If an error occurs during report generation, the `ReportService` returns `None`
        if not encoded_report:
            return self._create_error_response('An error occurred during report generation.')

        # Submit report to the source system
        export_result = self.source_system.export_pdf_report(
            SourceSystemReportExportData(
                mrn=serializer.validated_data.get('mrn'),
                site=serializer.validated_data.get('site'),
                base64_content=encoded_report,
                document_number='MU-8624',  # TODO: clarify where to get the value (currently set as a test document)
                document_date=timezone.now(),  # TODO: get the exact time of the report creation
            ),
        )

        if (
            not export_result
            or 'status' not in export_result
            or export_result['status'] == 'error'
        ):
            LOGGER.error('An error occurred while exporting a PDF report to the source system.')

        return response.Response(export_result)

    def _create_error_response(self, message: str) -> response.Response:
        # Log an error message
        LOGGER.error(message)
        return response.Response(
            {
                'status': 'error',
                'message': message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
