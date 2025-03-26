"""Collection of api views used to send data to opal app through the listener request relay."""
from django.http import HttpRequest, HttpResponse

from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import LegacyNotification, LegacyUsers


class AppHomeView(APIView):
    """Class to return home page required data."""

    _ignore_model_permissions = True

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle GET requests from `api/app/home`.

        Args:
            request: Http request made by the listener.

        Returns:
            Http response with the data needed to display the home view.
        """
        user_sernum = self.get_sernum(request)
        return Response({
            'unread_notification_count': self.get_unread_notification_count(user_sernum),
        })

    def get_unread_notification_count(self, sernum: int) -> int:
        """
        Get the number of unread notifications for a given user.

        Args:
            sernum: User sernum used to retrieve unread notifications count.

        Returns:
            Number of unread notifications.
        """
        return LegacyNotification.objects.filter(patientsernum=sernum, readstatus=0).count()

    def get_sernum(self, request: HttpRequest) -> int:
        """
        Get the user sernum associated with the username to query the legacy database.

        Args:
            request: The http request made by the listener

        Returns:
            User sernum associated with the request username user name.
        """
        username = request.headers['Userid']
        return LegacyUsers.objects.get(username=username).usertypesernum
