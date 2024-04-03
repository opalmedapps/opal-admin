"""Collection of api views used to display the Opal's General view."""
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.legacy import models
from opal.patients.models import Relationship, RelationshipStatus

from ..serializers import AnnouncementUnreadCountSerializer


class AppGeneralView(APIView):
    """Class to return general page required data."""

    permission_classes = (IsListener,)

    def get(self, request: Request) -> Response:
        """
        Handle GET requests from `api/app/general`.

        The function provides the number of unread values for the Opal app user.

        Args:
            request: HTTP request made by the listener.

        Returns:
            HTTP response with the data needed to display the general view.
        """
        unread_count = {
            'unread_announcement_count': models.LegacyAnnouncement.objects.get_unread_queryset(
                patient_sernum_list=Relationship.objects.get_list_of_patients_ids_for_caregiver(
                    username=request.headers['Appuserid'],
                    status=RelationshipStatus.CONFIRMED,
                ),
                username=request.headers['Appuserid'],
            ),
        }

        return Response(AnnouncementUnreadCountSerializer(unread_count).data)
