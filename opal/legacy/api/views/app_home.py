"""Collection of api views used to display the Opal's home view."""
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.legacy import models

from ..serializers import LegacyAppointmentSerializer


class AppHomeView(APIView):
    """Class to return home page required data."""

    permission_classes = (IsListener,)

    def get(self, request: Request) -> Response:
        """
        Handle GET requests from `api/app/home`.

        Args:
            request: Http request made by the listener.

        Returns:
            Http response with the data needed to display the home view.
        """
        username = request.headers['Appuserid']

        return Response({
            'unread_notification_count': models.LegacyNotification.objects.get_unread_multiple_patients_queryset(
                username,
            ).count(),
            'daily_appointments': LegacyAppointmentSerializer(
                models.LegacyAppointment.objects.get_daily_appointments(username),
                many=True,
            ).data,
            'closest_appointment': LegacyAppointmentSerializer(
                models.LegacyAppointment.objects.get_closest_appointment(username),
            ).data,
        })
