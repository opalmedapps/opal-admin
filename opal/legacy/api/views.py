"""Collection of api views used to send data to opal app through the listener request relay."""

from django.http import HttpRequest, HttpResponse

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.legacy.utils import get_patient_sernum

from .. import models
from .serializers import LegacyAppointmentSerializer


class AppHomeView(APIView):
    """Class to return home page required data."""

    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle GET requests from `api/app/home`.

        Args:
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


class AppChartView(APIView):
    """Class to return chart page required data."""

    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle GET requests from `api/app/chart`.

        Args:
            request: Http request made by the listener.

        Returns:
            Http response with the data needed to display the chart view.
        """
        patient_sernum = get_patient_sernum(request.headers['Appuserid'])
        return Response({
            'unread_appointment_count':
                models.LegacyAppointment.objects.get_unread_queryset(patient_sernum).count(),
            'unread_document_count':
                models.LegacyDocument.objects.get_unread_queryset(patient_sernum).count(),
            'unread_txteammessage_count':
                models.LegacyTxTeamMessage.objects.get_unread_queryset(patient_sernum).count(),
            'unread_educationalmaterial_count':
                models.LegacyEducationMaterial.objects.get_unread_queryset(patient_sernum).count(),
            'unread_questionnaire_count':
                models.LegacyQuestionnaire.objects.get_unread_queryset(patient_sernum).count(),
        })
