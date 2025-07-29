import base64
import json
from typing import Any

from django.shortcuts import get_object_or_404

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.patients.models import Patient


class GetPatientSummary(APIView):
    """Class to return an International Patient Summary (IPS) for a given patient."""

    permission_classes = (IsListener,)

    def get(self, request: Request, uuid: str, index: int) -> Response:
        """
        Handle GET requests from `patients/<uuid:uuid>/ips/`.

        Args:
            request: Http request made by the listener to retrieve the data for an IPS link.
            uuid: The patient's UUID for whom IPS link data is being generated.

        Returns:
            Http response with the data to build a SMART health link that can be parsed by IPS viewers.
        """
        patient = get_object_or_404(Patient, uuid=uuid)
        print('TESTTEST')
        print(index)

        # TODO temp test data
        # with open('../sample-bundle.json', encoding='utf-8') as f:
        #     d = json.load(f)
        #     print(d)

        if index == 0:
            # link_content = {
            #     'url': 'https://raw.githubusercontent.com/seanno/shc-demo-data/main/ips/IPS_IG-bundle-01-enc.txt',
            #     'flag': 'LU',
            #     'key': 'rxTgYlOaKJPFtcEd0qcceN8wEU4p94SqAwIWQe6uX7Q',
            #     'label': 'Demo SHL for IPS_IG-bundle-01',
            # }
            link_content = {
                'url': 'https://dev.app.opalmedapps.ca/content/test-ips-bundle.txt',
                'flag': 'LU',
                'key': 'rxTgYlOaKJPFtcEd0qcceN8wEU4p94SqAwIWQe6uX7Q',
                'label': 'Opal-App Demo',
            }
        else:
            # link_content = {
            #     'url': 'https://smart-health-links-server.cirg.washington.edu/api/shl/aYcbj-op42et3sMupIGrcWoCrIZIjy9exu0Zo0RygIo',
            #     'flag': '',
            #     'key': 'nwIE4X0lcaMno9zPwaDruv5dP9TD6E7bHrau9r9KlDQ',
            #     'label': 'SHL from 2023-09-10 ePatientDave #2b',
            # }
            link_content = {
                'url': 'https://dev.app.opalmedapps.ca/content/test-ips-bundle.txt',
                'flag': 'LU',
                'key': 'rxTgYlOaKJPFtcEd0qcceN8wEU4p94SqAwIWQe6uX7Q',
                'label': 'Opal-App Demo',
            }

        # Convert the link content into JSON, parse it as base64, and build the link data
        link_json = json.dumps(link_content, indent=None, separators=(',', ':'))
        link_base64 = base64.b64encode(link_json.encode('utf-8')).decode('utf-8')
        link_data = 'shlink:/' + link_base64

        # the result is a JSON string:
        print(link_data)

        return Response(
            link_data,
        )
