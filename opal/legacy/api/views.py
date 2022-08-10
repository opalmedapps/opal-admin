"""Collection of api views used to send data to opal app through the listener request relay."""

import json
from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

import requests
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.legacy.utils import get_patient_sernum

from ...services.hospital import OIECommunicationService
from ...services.reports import ReportService
from ..models import LegacyAppointment, LegacyNotification
from .serializers import LegacyAppointmentSerializer, QuestionnaireReportRequestSerializer


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


class QuestionnairesReportCreateAPIView(CreateAPIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = [IsAuthenticated]
    serializer_class = QuestionnaireReportRequestSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Generate questionnaire PDF report and submit to the OIE.

        Args:
            request (Request): HTTP request that initiates report generation
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            HTTP `Response` with results of report generation
        """
        serializer = QuestionnaireReportRequestSerializer(data=request.data)
        # Validate received data. Return a 400 response if the data was invalid.
        serializer.is_valid(raise_exception=True)

        # Generate questionnaire report
        report_service = ReportService()
        encoded_report = report_service.generate_questionnaire_report(
            request.data['patient_id'],
            request.data['language'],
        )

        if encoded_report == '':
            return Response(
                {
                    'status': 'error',
                    'message': 'Bad request: an error occured during report generation.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Submit report to the OIE
        oie = OIECommunicationService()
        json_response = json.loads(oie.export_questionnaire_report(encoded_report).content)

        # Try to decode JSON response
        try:
            # If HTTP status code is not success (e.g, different than 2**)
            if json_response['status'] != status.HTTP_200_OK:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Bad request: {0}'.format(json_response['message']),
                    },
                    status=json_response['status'],
                )
        except requests.exceptions.JSONDecodeError:
            return Response(
                {
                    'status': 'error',
                    'message': 'Bad request: an error occured while decoding the JSON object received from the OIE.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except KeyError:
            return Response(
                {
                    'status': 'error',
                    'message':
                    (
                        'Bad request: '
                        + 'an error occured while accessing a key in the JSON object received from the OIE.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(json_response)
