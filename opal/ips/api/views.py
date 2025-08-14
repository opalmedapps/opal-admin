import base64
import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.patients.models import Patient
from opal.services.data_upload.data_upload import DataUpload
from opal.services.fhir.fhir import FhirCommunication


class GetPatientSummary(APIView):
    """Class to return an International Patient Summary (IPS) for a given patient."""

    permission_classes = (IsListener,)

    def get(self, request: Request, uuid: str) -> HttpResponse | Response:
        """
        Handle GET requests from `patients/<uuid:uuid>/ips/`.

        Assemble the data needed to build a Smart Health Link that can be read by an IPS viewer.

        Args:
            request: Http request made by the listener to retrieve the data for an IPS link.
            uuid: The patient's UUID for whom IPS link data is being generated.

        Returns:
            Http response with the data to build a SMART health link that can be parsed by IPS viewers.
        """
        # Validate the patient's existence
        patient = get_object_or_404(Patient, uuid=uuid)

        try:
            # Request and assemble IPS data into a bundle
            fhir = FhirCommunication('OpenEMR')
            fhir.connect()
            ips = fhir.assemble_ips(ramq=patient.ramq)

            # TODO generate key
            encryption_key = 'rxTgYlOaKJPFtcEd0qcceN8wEU4p94SqAwIWQe6uX7Q'
            encryption_key_bytes = b'rxTgYlOaKJPFtcEd0qcceN8wEU4p94SqAwIWQe6uX7Q'
            encrypted_ips = fhir.encrypt_shlink_file(ips, encryption_key_bytes)

            # Upload the IPS bundle to the FTP server used to serve these bundles
            uploader = DataUpload()
            uploader.upload('app/dev/content/ips/bundles', f'ips-bundle_{uuid}.txt', encrypted_ips)

        except NotImplementedError as error:
            return HttpResponse(str(error), status=status.HTTP_501_NOT_IMPLEMENTED)

        # See: https://docs.smarthealthit.org/smart-health-links/spec/#construct-a-shlink-payload
        link_content = {
            'url': f'https://dev.app.opalmedapps.ca/content/ips/manifest-request/{uuid}',
            'flag': 'L',
            'key': encryption_key,
            'label': 'Opal-App IPS Demo',
        }

        # Convert the link content into JSON, parse it as base64, and build the link data
        link_json = json.dumps(link_content, indent=None, separators=(',', ':'))
        link_base64 = base64.b64encode(link_json.encode('utf-8')).decode('utf-8')
        link_data = 'shlink:/' + link_base64

        return Response(
            link_data,
        )
