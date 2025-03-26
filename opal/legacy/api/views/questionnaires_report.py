"""Collection of api views used to send questionnaire PDF reports to the OIE."""

import logging
from pathlib import Path
from typing import Any

from django.utils import timezone, translation

from rest_framework import generics, permissions
from rest_framework import request as rest_request
from rest_framework import response, status

from opal.hospital_settings.models import Institution
from opal.patients.models import HospitalPatient
from opal.services import hospital, reports

from ..serializers import QuestionnaireReportRequestSerializer


class QuestionnairesReportCreateAPIView(generics.CreateAPIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuestionnaireReportRequestSerializer
    # Get an instance of a logger
    logger = logging.getLogger(__name__)

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
        with translation.override(request.headers['Accept-Language']):  # TODO: override the language in a middleware
            serializer = QuestionnaireReportRequestSerializer(data=request.data)
            # Validate received data. Return a 400 response if the data was invalid.
            serializer.is_valid(raise_exception=True)

            # Generate questionnaire report
            report_service = reports.ReportService()
            encoded_report = report_service.generate_questionnaire_report(
                reports.QuestionnaireReportRequestData(
                    patient_id=int(request.data['patient_id']),
                    logo_path=Path(Institution.objects.get(pk=1).logo.path),
                    language=request.headers['Accept-Language'],
                ),
            )

            if encoded_report == '':
                # Log an error message
                self.logger.error('An error occured during report generation.')
                return response.Response(
                    {
                        'status': 'error',
                        'message': 'An error occured during report generation.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Submit report to the OIE
            oie = hospital.OIEService()
            export_result = oie.export_pdf_report(
                hospital.OIEReportExportData(
                    mrn=HospitalPatient.objects.filter(
                        patient__legacy_id=serializer.validated_data.patient_id,
                    ).values_list('mrn', flat=True).get(pk=1),
                    site=HospitalPatient.objects.filter(
                        patient__legacy_id=serializer.validated_data.patient_id,
                    ).values_list('site__name', flat=True).get(pk=1),
                    base64_content=encoded_report,
                    document_number='FMU',  # TODO: clarify where to get the value
                    document_date=timezone.localtime(timezone.now()),  # TODO: get the exact time of the report creation
                ),
            )

            if 'status' not in export_result or export_result['status'] == 'error':
                self.logger.error('An error occured while exporting a PDF report to the OIE.')

            return response.Response(export_result)
