# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Collection of api views used to send questionnaire PDF reports to the source system."""

import base64
import logging
from typing import Any

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from fpdf import FPDFException
from rest_framework import exceptions, response, views
from rest_framework.request import Request

from opal.core.drf_permissions import IsORMSUser
from opal.legacy.utils import generate_questionnaire_report, get_questionnaire_data
from opal.patients.models import Patient
from opal.services.integration import hospital

from ..serializers import QuestionnaireReportRequestSerializer

LOGGER = logging.getLogger(__name__)


class QuestionnairesReportView(views.APIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = (IsORMSUser,)
    serializer_class = QuestionnaireReportRequestSerializer

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

        mrn = serializer.validated_data.get('mrn')
        site = serializer.validated_data.get('site')

        try:
            patient = Patient.objects.get_patient_by_site_mrn_list(
                [
                    {
                        'site': {'acronym': site},
                        'mrn': mrn,
                    },
                ],
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned) as error:
            raise exceptions.ParseError(
                detail='Could not find `Patient` record with the provided MRN and site acronym.',
            ) from error

        # Generate questionnaire report
        try:
            pdf_report = generate_questionnaire_report(patient, get_questionnaire_data(patient))
        except FPDFException as exc:
            LOGGER.exception('An error occurred during questionnaire report generation')
            raise exceptions.APIException(detail='An error occurred during questionnaire report generation.') from exc

        encoded_report = base64.b64encode(pdf_report)

        try:
            hospital.add_questionnaire_report(mrn, site, encoded_report)
        except hospital.NonOKResponseError as exc:
            LOGGER.exception('An error occurred while exporting a PDF report to the source system')
            raise exceptions.APIException(
                detail='An error occurred while exporting a PDF report to the source system'
            ) from exc
        except hospital.PatientNotFoundError as exc:
            LOGGER.exception('The patient was not found in the source system')
            raise exceptions.APIException(detail='The patient was not found in the source system') from exc

        return response.Response()
