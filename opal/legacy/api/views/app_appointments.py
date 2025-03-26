"""Collection of api views used to get appointment details."""
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.legacy import models

from ..serializers import LegacyAppointmentDetailedSerializer


@extend_schema(
    responses=inline_serializer(
        name='AppAppointmentsSerializer',
        fields={
            'daily_appointments': LegacyAppointmentDetailedSerializer(many=True),
        },
    ),
)
class AppAppointmentsView(APIView):
    """Class to return appointments detail data."""

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
            'daily_appointments': LegacyAppointmentDetailedSerializer(
                models.LegacyAppointment.objects.get_daily_appointments(username),
                many=True,
            ).data,
        })
