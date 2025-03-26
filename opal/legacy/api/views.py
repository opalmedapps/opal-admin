"""Collection of api views used to send data to opal app through the listener request relay."""

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.legacy.utils import get_patient_sernum

from ..models import LegacyAppointment, LegacyNotification
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
            'unread_notification_count': self.get_unread_notification_count(patient_sernum),
            'daily_appointments': LegacyAppointmentSerializer(
                self.get_daily_appointments(patient_sernum),
                many=True,
            ).data,
        })

    def get_daily_appointments(self, patient_sernum: int) -> QuerySet[LegacyAppointment]:
        """
        Get all appointment for the current day.

        Args:
            patient_sernum: Patient sernum used to retrieve unread notifications count.

        Returns:
            Appointments schedule for the current day.
        """
        return LegacyAppointment.objects.select_related(
            'aliasexpressionsernum',
            'aliasexpressionsernum__aliassernum',
            'aliasexpressionsernum__aliassernum__appointmentcheckin',
        ).filter(
            scheduledstarttime__date=timezone.localtime(timezone.now()).date(),
            patientsernum=patient_sernum,
            state='Active',
        ).exclude(
            status='Deleted',
        )

    def get_unread_notification_count(self, sernum: int) -> int:
        """
        Get the number of unread notifications for a given user.

        Args:
            sernum: User sernum used to retrieve unread notifications count.

        Returns:
            Number of unread notifications.
        """
        return LegacyNotification.objects.filter(patientsernum=sernum, readstatus=0).count()
