"""Collection of api views used to send data to opal app through the listener request relay."""

from typing import Any

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from opal.legacy.utils import get_patient_sernum

from .. import models
from .serializers import LegacyAppointmentSerializer, UnreadCountSerializer


class AppHomeView(RetrieveAPIView):
    """Class to return home page required data."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle GET requests from `api/app/home`.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
            request: Http request made by the listener.

        Returns:
            Http response with the data needed to display the home view.
        """
        patient_sernum = get_patient_sernum(request.headers['Appuserid'])
        return Response({
            'unread_notification_count': models.LegacyNotification.objects.get_unread_queryset(patient_sernum).count(),
            'daily_appointments': LegacyAppointmentSerializer(
                models.LegacyAppointment.objects.get_daily_appointments(patient_sernum),
                many=True,
            ).data,
        })


class AppChartView(ListAPIView):
    """Class to return chart page required data."""

    permission_classes = [IsAuthenticated]

    def get(self, *args: Any, **kwargs: Any) -> Response:
        """
        Handle GET requests from `api/app/chart`.

        The function provides the number of unread values for the user
        and will provide them for the selected patient instead until the profile selector is finished.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            Http response with the data needed to display the chart view.
        """
        legacy_id = kwargs['legacy_id']
        unread_count = {
            'unread_appointment_count': models.LegacyAppointment.objects.get_unread_queryset(legacy_id).count(),
            'unread_document_count': models.LegacyDocument.objects.get_unread_queryset(legacy_id).count(),
            'unread_txteammessage_count': models.LegacyTxTeamMessage.objects.get_unread_queryset(
                legacy_id,
            ).count(),
            'unread_educationalmaterial_count': models.LegacyEducationalMaterial.objects.get_unread_queryset(
                legacy_id,
            ).count(),
            'unread_questionnaire_count': models.LegacyQuestionnaire.objects.get_unread_queryset(
                legacy_id,
            ).count(),
        }

        return Response(UnreadCountSerializer(unread_count).data)
