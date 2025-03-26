"""Collection of api views used to send questionnaire PDF reports to the OIE."""

import logging
from pathlib import Path
from typing import Any

from django.utils import timezone

from rest_framework import permissions
from rest_framework import request as rest_request
from rest_framework import response, status
from rest_framework.views import APIView

from opal.hospital_settings.models import Institution
from opal.patients.models import HospitalPatient
from opal.services import hospital, reports

from ..serializers import QuestionnaireReportRequestSerializer


class QuestionnairesReportCreateAPIView(APIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuestionnaireReportRequestSerializer
    # Get an instance of a logger
    logger = logging.getLogger(__name__)
    # OIE service
    oie = hospital.OIEService()
    # Report service
    report_service = reports.ReportService()

    def post(
        self,
        request: rest_request.Request,
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

        # Generate questionnaire report
        encoded_report = self.report_service.generate_questionnaire_report(
            reports.QuestionnaireReportRequestData(
                patient_id=serializer.validated_data.get('patient_id'),
                logo_path=Path(Institution.objects.get(pk=1).logo.path),
                language=request.headers['Accept-Language'],
            ),
        )

        # The `ReportService` does not return error messages.
        # If an error occurs during report generation, the `ReportService` returns `None`
        if not encoded_report:
            return self._create_error_response('An error occurred during report generation.')

        hospital_patient = HospitalPatient.objects.select_related(
            'site',
        ).filter(
            patient__legacy_id=serializer.validated_data.get('patient_id'),
        ).first()

        if not hospital_patient:
            return self._create_error_response(
                'Could not find `HospitalPatient` object for the given `patient_id`.',
            )

        # Submit report to the OIE
        export_result = self.oie.export_pdf_report(
            hospital.OIEReportExportData(
                mrn=hospital_patient.mrn,
                site=hospital_patient.site.name,
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
