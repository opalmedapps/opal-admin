"""This module provides `APIViews` for the report settings REST API."""
import json
from typing import Any

from django.conf import settings

import requests
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import QuestionnaireReportRequestSerializer


class QuestionnairesReportCreateAPIView(CreateAPIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = [IsAuthenticated]
    serializer_class = QuestionnaireReportRequestSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Generate questionnaires PDF report and submit to OIE.

        Args:
            request: HTTP request that initiates report generation
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments

        Returns:
            HTTP `Response` with results of report generation
        """
        serializer = QuestionnaireReportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'data': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        pload = json.dumps({
            'patient_id': 51,
            'patient_name': 'Test name',
            'patient_mrn': '999996',
            'patient_language': 'FR',
        })
        headers = {'Content-Type': 'application/json'}
        response = requests.post(settings.LEGACY_QUESTIONNAIRES_REPORT_URL, headers=headers, data=pload)

        # TODO: call OIE
        return Response({'status': response.status_code, 'data': response.content}, status=status.HTTP_200_OK)
