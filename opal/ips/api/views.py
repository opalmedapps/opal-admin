import base64
import json

from django.shortcuts import get_object_or_404

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.patients.models import Patient


class GetPatientSummary(APIView):
    """Class to return an International Patient Summary (IPS) for a given patient."""

    permission_classes = (IsListener,)

    def get(self, request: Request, uuid: str) -> Response:
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
        get_object_or_404(Patient, uuid=uuid)

        # See: https://docs.smarthealthit.org/smart-health-links/spec/#construct-a-shlink-payload
        link_content = {
            'url': f'http://localhost:8000/api/patients/{uuid}/ips/manifest-request/',
            'flag': 'L',
            # TODO generate key
            'key': 'rxTgYlOaKJPFtcEd0qcceN8wEU4p94SqAwIWQe6uX7Q',
            'label': 'Opal-App Demo',
        }

        # Convert the link content into JSON, parse it as base64, and build the link data
        link_json = json.dumps(link_content, indent=None, separators=(',', ':'))
        link_base64 = base64.b64encode(link_json.encode('utf-8')).decode('utf-8')
        link_data = 'shlink:/' + link_base64

        return Response(
            link_data,
        )


class ManifestRequest(APIView):
    """Class to make a manifest request that will deliver an International Patient Summary (IPS) for a given patient."""

    # Allow unauthenticated access
    permission_classes = ()

    # Manifest request: https://docs.smarthealthit.org/smart-health-links/spec/#shlink-manifest-request
    def post(self, request: Request, uuid: str) -> Response:
        """
        Handle POST requests to `patients/<uuid:uuid>/ips/manifest-request/`.

        Fulfill Smart Health Link Manifest Requests.

        Args:
            request: Http request made by third-party applications to display a patient's IPS.
            uuid: The patient's UUID for whom to view the IPS.

        Returns:
            Http response with the data needed to request a patient's IPS bundle.
        """
        response = {
            'files': [
                {
                    'contentType': 'application/fhir+json',
                    # TODO supposed to be short-lived
                    'location': 'https://dev.app.opalmedapps.ca/content/test-ips-bundle.txt',
                },
            ]
        }

        return Response(
            response,
        )
