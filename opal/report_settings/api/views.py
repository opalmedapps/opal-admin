"""This module provides `APIViews` for the report settings REST API."""
from typing import Any

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

        # TODO: call php legacy backend
        # TODO: call OIE
        return Response({'status': 'success', 'data': ''}, status=status.HTTP_200_OK)
