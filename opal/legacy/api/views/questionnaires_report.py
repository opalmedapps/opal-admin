"""Collection of api views used to send questionnaire PDF reports to the OIE."""

import logging
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils import timezone, translation

from rest_framework import permissions, response, status, views
from rest_framework.request import Request

from opal.hospital_settings.models import Institution
from opal.patients.models import Patient
from opal.services.hospital.hospital import OIEReportExportData, OIEService
from opal.services.reports import QuestionnaireReportRequestData, ReportService

from ..serializers import QuestionnaireReportRequestSerializer


class QuestionnairesReportView(views.APIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuestionnaireReportRequestSerializer
    # Get an instance of a logger
    logger = logging.getLogger(__name__)
    # OIE service
    oie = OIEService()
    # Report service
    report_service = ReportService()

    def post(
        self,
        request: Request,
        *args: Any,
        **kwargs: Any,
    ) -> response.Response:
        """
        Generate questionnaire PDF report and submit to the OIE.

        Args:
            request (Request): HTTP request that initiates report generation
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

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

        # the language used in the current thread
        # if the language is not set (e.g., translations are temporarily deactivated), use the default language
        lang = translation.get_language() or settings.LANGUAGES[0][0]

        # Generate questionnaire report
        encoded_report = self.report_service.generate_base64_questionnaire_report(
            QuestionnaireReportRequestData(
                patient_id=patient.legacy_id if patient.legacy_id else -1,
                patient_name=f'{patient.first_name} {patient.last_name}',
                patient_site=serializer.validated_data.get('site'),
                patient_mrn=serializer.validated_data.get('mrn'),
                logo_path=Path(Institution.objects.get().logo.path),
                language=lang,
            ),
        )

        # The `ReportService` does not return error messages.
        # If an error occurs during report generation, the `ReportService` returns `None`
        if not encoded_report:
            return self._create_error_response('An error occurred during report generation.')

        # Submit report to the OIE
        export_result = self.oie.export_pdf_report(
            OIEReportExportData(
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
            self.logger.error('An error occurred while exporting a PDF report to the OIE.')

        return response.Response(export_result)

    def _create_error_response(self, message: str) -> response.Response:
        # Log an error message
        self.logger.error(message)
        return response.Response(
            {
                'status': 'error',
                'message': message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
