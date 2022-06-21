"""This module provides `APIViews` for the report settings REST API."""
import json
from typing import Any

import requests
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from opal.core.services.hospital import OIECommunicationService
from opal.core.services.reports import QuestionnaireReportService

from .serializers import QuestionnaireReportRequestSerializer


class QuestionnairesReportCreateAPIView(CreateAPIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = [IsAuthenticated]
    serializer_class = QuestionnaireReportRequestSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Generate questionnaires PDF report and submit to the OIE.

        Args:
            request: HTTP request that initiates report generation
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments

        Returns:
            HTTP `Response` with results of report generation
        """
        serializer = QuestionnaireReportRequestSerializer(data=request.data)
        # Validate received data. Return a 400 response if the data was invalid.
        serializer.is_valid(raise_exception=True)

        # Generate questionnaire report
        report_service = QuestionnaireReportService()
        encoded_report = report_service.generate(
            request.data['patient_id'],
            request.data['language'],
        )

        if encoded_report == '':
            return Response(
                {
                    'status': 'error',
                    'data': 'Bad request: an error occured during report generation.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Submit report to the OIE
        oie = OIECommunicationService()
        json_response = json.loads(oie.export_questionnaire_report(encoded_report).content)

        # Try to decode JSON response
        try:
            # If HTTP status code is not success (e.g, different than 2**)
            if json_response['status'] != status.HTTP_200_OK:
                return Response(
                    {
                        'status': 'error',
                        'data': 'Bad request: {0}'.format(json_response['message']),
                    },
                    status=json_response['status'],
                )
        except requests.exceptions.JSONDecodeError:
            return Response(
                {
                    'status': 'error',
                    'data': 'Bad request: an error occured while decoding the JSON object received from the OIE.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except KeyError:
            return Response(
                {
                    'status': 'error',
                    'data':
                    (
                        'Bad request: '
                        + 'an error occured while accessing a key in the JSON object received from the OIE.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(json_response)
