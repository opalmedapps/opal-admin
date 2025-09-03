import base64
import json
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string

import structlog
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.patients.models import Patient
from opal.services.fhir.utils import build_patient_summary, jwe_sh_link_encrypt

LOGGER = structlog.get_logger()


class GetPatientSummary(APIView):
    """Class to return an International Patient Summary (IPS) for a given patient."""

    permission_classes = (IsListener,)

    def get(self, request: Request, uuid: str) -> HttpResponse | Response:
        """
        Handle GET requests from `patients/<uuid:uuid>/ips/`.

        Assemble the data needed to build a Smart Health Link that can be read by an IPS viewer.

        Args:
            request: HTTP request
            uuid: the patient's UUID for whom IPS link data is being generated

        Returns:
            Http response with the SH link payload that can be parsed by IPS viewers
        """
        patient = get_object_or_404(Patient, uuid=uuid)

        # Request and assemble IPS data into a bundle
        private_key = settings.FHIR_API_PRIVATE_KEY
        ips = build_patient_summary(
            settings.FHIR_API_OAUTH_URL,
            settings.FHIR_API_URL,
            settings.FHIR_API_CLIENT_ID,
            private_key,
            patient.ramq,
        )

        # Generate an encryption key for the bundle, and encrypt it
        encryption_key, encrypted_ips = jwe_sh_link_encrypt(ips)

        storage_backend_class = import_string(settings.IPS_STORAGE_BACKEND)
        storage_backend = storage_backend_class()
        file_name = f'ips-bundle_{uuid}.txt'

        LOGGER.debug(
            'Saving IPS bundle for patient %s to %s using storage backend %s', uuid, file_name, storage_backend_class
        )

        if storage_backend.exists(file_name):
            LOGGER.debug('IPS bundle for patient %s already exists, deleting the existing one first', uuid)
            storage_backend.delete(file_name)

        storage_backend.save(file_name, BytesIO(encrypted_ips))
        LOGGER.debug('Successfully saved IPS bundle for patient %s to %s', uuid, file_name)

        # See: https://docs.smarthealthit.org/smart-health-links/spec/#construct-a-shlink-payload
        link_content = {
            'url': f'{settings.IPS_PUBLIC_BASE_URL}/{uuid}',
            'flag': 'L',
            'key': encryption_key,
            'label': 'Opal-App IPS Demo',
        }

        LOGGER.debug('Constructed SH link content for patient %s', uuid, extra=link_content)

        # Convert the link content into JSON, parse it as base64, and build the SH link payload
        link_json = json.dumps(link_content, indent=None, separators=(',', ':'))
        link_base64 = base64.b64encode(link_json.encode('utf-8')).decode('utf-8')
        link_data = 'shlink:/' + link_base64

        return Response(
            link_data,
        )
