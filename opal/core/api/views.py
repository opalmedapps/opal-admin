"""Module providing reusable views for the whole project."""

import uuid
from typing import Any, TypeVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_parsers.hl7_parser import HL7Parser
from opal.core.drf_permissions import IsRegistrationListener
from opal.hospital_settings.models import Site
from opal.patients.models import Patient

from .serializers import LanguageSerializer

_Model = TypeVar('_Model', bound=Model)


@extend_schema(
    responses={
        200: LanguageSerializer(many=True),
    },
)
class LanguagesView(APIView):
    """View that returns the list of supported languages."""

    permission_classes = (IsRegistrationListener,)

    def get(self, request: HttpRequest) -> Response:
        """
        Handle GET requests to list the supported languages.

        Args:
            request: the HTTP request

        Returns:
            HTTP response with a list of languages
        """
        data = [{'code': code, 'name': name} for (code, name) in settings.LANGUAGES]
        response = LanguageSerializer(data, many=True).data
        return Response(response)


class HL7CreateView(CreateAPIView[_Model]):
    """APIView Superclass for all endpoints requiring HL7 parsing."""

    parser_classes = (HL7Parser,)

    def get_parser_context(self, http_request: HttpRequest) -> dict[str, Any]:
        """Append a list of HL7 segments to be parsed to the dictionary of parser context data.

        Each view can define segments_to_parse if desired to add specific segments to parse.

        Args:
            http_request: The incoming request

        Returns:
            parser context for the HL7Parser.parse() method
        """
        context = super().get_parser_context(http_request)
        context['segments_to_parse'] = getattr(self, 'segments_to_parse', None)
        return context

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Ensure the patient identified in kwargs uniquely exists and matches the PID data.

        Args:
            request: The http request object
            args: Any number of additional arguments
            kwargs: Any number of key word arguments

        Returns:
            API Response with code and headers
        """
        if not self._validate_uuid_matches_pid_segment(request.data, self.kwargs['uuid']):
            return Response(
                {
                    'status': 'error',
                    'message': 'PID segment data did not match uuid provided in url.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient: Patient = get_object_or_404(Patient, uuid=self.kwargs['uuid'])
        request.data['patient'] = patient
        return super().post(request, *args, **kwargs)

    def _validate_uuid_matches_pid_segment(
        self,
        parsed_data: dict[str, Any],
        url_uuid: uuid.UUID,
    ) -> bool:
        """Ensure the PID segment parsed from the message matches the uuid from the url.

        Args:
            parsed_data: segmented dictionary parsed from the HL7 request data
            url_uuid: UUID string passed in the endpoint url kwarg

        Raises:
            ValidationError: If no patient could be found at all, or multiple are found

        Returns:
            True if the patient identified in the PID segment exists in the database and matches the UUID
        """
        # Filter out invalid sites from the raw site list given by the hospital (e.g `HNAM_PERSONID`)
        valid_sites = {site_tuple[0] for site_tuple in Site.objects.all().values_list('acronym')}
        valid_pid_mrn_sites = [
            mrn_site for mrn_site in parsed_data.get('PID', None)['mrn_sites'] if mrn_site[1] in valid_sites
        ]
        try:
            patient = Patient.objects.get_patient_by_site_mrn_list(
                site_mrn_list=[
                    {
                        'site': {'acronym': site},
                        'mrn': mrn,
                    } for mrn, site in valid_pid_mrn_sites
                ],
            )
        except (Patient.DoesNotExist, Patient.MultipleObjectsReturned):
            raise ValidationError('Patient identified by HL7 PID could not be uniquely found in database.')
        return url_uuid == patient.uuid
