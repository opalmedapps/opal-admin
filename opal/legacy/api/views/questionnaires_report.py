"""Collection of api views used to send questionnaire PDF reports to the source system."""

import base64
import logging
from typing import Any

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils import timezone

from fpdf import FPDFException
from rest_framework import exceptions, response, views
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

        Raises:
            ParseError: if the patient can not be found
            APIException: if the report generation fails
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
            raise exceptions.ParseError(
                detail='Could not find `Patient` record with the provided MRN and site acronym.',
            )

        # Generate questionnaire report
        try:
            pdf_report = generate_questionnaire_report(patient, get_questionnaire_data(patient))
        except FPDFException as exc:
            LOGGER.exception(exc)
            raise exceptions.APIException(detail='An error occurred during report generation.')

        encoded_report = base64.b64encode(pdf_report).decode('utf-8')

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
            LOGGER.error(f'An error occurred while exporting a PDF report to the source system: {export_result}')
            raise exceptions.APIException(detail='An error occurred while exporting a PDF report to the source system')

        return response.Response()
