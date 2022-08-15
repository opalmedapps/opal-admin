"""Collection of api views used to send data to opal app through the listener request relay."""

import logging
from pathlib import Path
from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils import timezone, translation

from rest_framework import generics, permissions, response, status, views
from rest_framework.request import Request

from opal.hospital_settings.models import Institution
from opal.legacy.utils import get_patient_sernum
from opal.patients.models import HospitalPatient
from opal.services import hospital, reports

from ..models import LegacyAppointment, LegacyNotification
from .serializers import LegacyAppointmentSerializer, QuestionnaireReportRequestSerializer


class AppHomeView(views.APIView):
    """Class to return home page required data."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle GET requests from `api/app/home`.

        Args:
            request: Http request made by the listener.

        Returns:
            Http response with the data needed to display the home view.
        """
        patient_sernum = get_patient_sernum(request.headers['Appuserid'])
        return response.Response({
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


class QuestionnairesReportCreateAPIView(generics.CreateAPIView):
    """View to generate a questionnaires PDF report."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuestionnaireReportRequestSerializer

    def post(
        self,
        request: Request,
        *args: Any,
        **kwargs: Any,
    ) -> response.Response:
        """
        Generate questionnaire PDF report and submit to the OIE.

        Args:
            request (Request): HTTP request that initiates report generation
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            HTTP `Response` with results of report generation
        """
        # Get an instance of a logger
        logger = logging.getLogger(__name__)

        with translation.override(request.headers['Accept-Language']):  # TODO: override the language in a middleware
            serializer = QuestionnaireReportRequestSerializer(data=request.data)
            # Validate received data. Return a 400 response if the data was invalid.
            serializer.is_valid(raise_exception=True)

            # Generate questionnaire report
            report_service = reports.ReportService()
            encoded_report = report_service.generate_questionnaire_report(
                reports.QuestionnaireReportRequestData(
                    patient_id=int(request.data['patient_id']),
                    logo_path=Path(Institution.objects.get(pk=1).logo.path),
                    language=request.headers['Accept-Language'],
                ),
            )

            if encoded_report == '':
                err_msg = 'An error occured during report generation.'
                # Log an error message
                logger.error(err_msg)
                return response.Response(
                    {
                        'status': 'error',
                        'message': err_msg,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Submit report to the OIE
            oie = hospital.OIEService()
            export_result = oie.export_pdf_report(
                hospital.OIEReportExportData(
                    mrn=HospitalPatient.objects.filter(
                        patient__legacy_id=serializer.validated_data.patient_id,
                    ).values_list('mrn', flat=True).get(pk=1),
                    site=HospitalPatient.objects.filter(
                        patient__legacy_id=serializer.validated_data.patient_id,
                    ).values_list('site__name', flat=True).get(pk=1),
                    base64_content=encoded_report,
                    document_number='FMU',  # TODO: clarify where to get the value
                    document_date=timezone.localtime(timezone.now()),  # TODO: get the exact time of the report creation
                ),
            )

            if 'status' not in export_result or export_result['status'] == 'error':
                logger.error('An error occured while exporting a PDF report to the OIE.')

            return response.Response(export_result)
