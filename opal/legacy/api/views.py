"""Collection of api views used to send data to opal app through the listener request relay."""

from typing import Any

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import CaregiverPatientPermissions

from .. import models
from ..utils import get_patient_sernum
from .serializers import AnnouncementUnreadCountSerializer, LegacyAppointmentSerializer, UnreadCountSerializer


class AppHomeView(APIView):
    """Class to return home page required data."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
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


class CaregiverPermissionsView(APIView):
    """
    Bare-bones API view used to perform a simple caregiver-patient permissions check.

    Validates that a caregiver has permission to view data for a specific patient (based on their relationship).
    Used by the legacy part of the listener to access functionality from CaregiverPatientPermissions.
    """

    # The essential work for this request is done by CaregiverPatientPermissions
    permission_classes = [IsAuthenticated, CaregiverPatientPermissions]

    def get(self, request: Request, legacy_id: int) -> Response:
        """
        Handle GET requests on `patients/legacy/<legacy_id>/check_permissions`.

        Args:
            request: Http request made by the listener.
            legacy_id: The legacy ID used to represent the target patient.

        Returns:
            Http response containing no data if the permission checks succeed (200 OK), or a permission denied
            response if the permission checks fail.
        """
        # The following empty success response is only returned if CaregiverPatientPermissions succeeds
        return Response({})


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
        patient_sernum = get_patient_sernum(request.headers['Appuserid'])
        unread_count = {
            'unread_announcement_count': models.LegacyAnnouncement.objects.get_unread_queryset(
                patient_sernum,
            ).count(),
        }
        return Response(AnnouncementUnreadCountSerializer(unread_count).data)
