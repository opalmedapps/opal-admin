"""Collection of api views used to display the Opal's Chart view."""

from typing import Any

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.legacy import models

from ..serializers import UnreadCountSerializer


class AppChartView(APIView):
    """Class to return chart page required data."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle GET requests from `api/app/chart`.

        The function provides the number of unread values for the user
        and will provide them for the selected patient instead until the profile selector is finished.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
            request: http request use to get username making the request

        Returns:
            Http response with the data needed to display the chart view.
        """
        legacy_id = kwargs['legacy_id']
        user_name = request.headers['Appuserid']
        unread_count = {
            'unread_appointment_count': models.LegacyAppointment.objects.get_unread_queryset(
                legacy_id,
                user_name,
            ).count(),
            'unread_document_count': models.LegacyDocument.objects.get_unread_queryset(
                legacy_id,
                user_name,
            ).count(),
            'unread_txteammessage_count': models.LegacyTxTeamMessage.objects.get_unread_queryset(
                legacy_id,
                user_name,
            ).count(),
            'unread_educationalmaterial_count': models.LegacyEducationalMaterial.objects.get_unread_queryset(
                legacy_id,
                user_name,
            ).count(),
            'unread_questionnaire_count': models.LegacyQuestionnaire.objects.get_unread_queryset(
                legacy_id,
            ).count(),
        }

        return Response(UnreadCountSerializer(unread_count).data)
