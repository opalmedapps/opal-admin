"""Collection of api views used to display the Opal's General view."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.legacy import models
from opal.patients.models import Relationship

from ..serializers import AnnouncementUnreadCountSerializer


class AppGeneralView(APIView):
    """Class to return general page required data."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Handle GET requests from `api/app/general`.

        The function provides the number of unread values for the user
        and will provide them for the selected patient instead until the profile selector is finished.

        Args:
            request: Http request made by the listener.

        Returns:
            Http response with the data needed to display the general view.
        """
        unread_count = {
            'unread_announcement_count': models.LegacyAnnouncement.objects.get_unread_queryset(
                Relationship.objects.get_patient_id_list_for_caregiver(request.headers['Appuserid']),
                request.headers['Appuserid'],
            ),
        }
        return Response(AnnouncementUnreadCountSerializer(unread_count).data)
