"""Collection of api views used to send questionnaire PDF reports to the OIE."""

import logging
from pathlib import Path
from typing import Any

from django.utils import timezone

from rest_framework import permissions, response, status
from rest_framework.request import Request
from rest_framework.views import APIView

from opal.hospital_settings.models import Institution
from opal.patients.models import HospitalPatient
from opal.services.hospital.hospital import OIEReportExportData, OIEService
from opal.services.reports import QuestionnaireReportRequestData, ReportService

from ..serializers import QuestionnaireReportRequestSerializer


class QuestionnairesReportView(APIView):
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
        if 'Accept-Language' not in request.headers:
            return self._create_error_response('The request does not contain the "Accept-Language" header.')

        serializer = QuestionnaireReportRequestSerializer(data=request.data)
        # Validate received data. Return a 400 response if the data was invalid.
        serializer.is_valid(raise_exception=True)

        hospital_patient = HospitalPatient.objects.select_related(
            'site',
            'patient',
        ).filter(
            mrn=serializer.validated_data.get('mrn'),
            site__name=serializer.validated_data.get('site_name'),
        ).first()

        if (
            not hospital_patient
            or not hospital_patient.patient
            or not hospital_patient.patient.legacy_id
        ):
            return self._create_error_response(
                'Could not find `HospitalPatient` object data.',
            )

        # Generate questionnaire report
        encoded_report = self.report_service.generate_questionnaire_report(
            QuestionnaireReportRequestData(
                patient_id=hospital_patient.patient.legacy_id,
                logo_path=Path(Institution.objects.get(pk=1).logo.path),
                language=request.headers['Accept-Language'],
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
                site=serializer.validated_data.get('site_name'),
                base64_content=encoded_report,
                document_number='FMU',  # TODO: clarify where to get the value
                document_date=timezone.localtime(timezone.now()),  # TODO: get the exact time of the report creation
            ),
        )

        if 'status' not in export_result or export_result['status'] == 'error':
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
