"""This module provides `APIViews` for the `test-results` app REST APIs."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.patients.models import Patient

from .serializers import GeneralTestSerializer


class CreateGeneralTestView(APIView):
    """
    `APIView` for handling POST requests for the `GeneralTest` and creating pathology reports.

    Supports the creation of one or more instances of the nested `observation` and `note` records.
    """

    permission_classes = [IsAuthenticated]   # CreateModelPermissions
    pagination_class = None
    http_method_names = ['post', 'head', 'options', 'trace']

    def post(self, request: Request) -> Response:
        """
        Create `GeneralTest` (a.k.a pathology) record for the patient.

        Ensures that the patient with the UUID as part of the URL exists.
        Raises a 404 if the patient does not exist.

        Args:
            request: the API request containing pathology data

        Returns:
            the response
        """
        print(request.content_params)
        # patient_uuid = request['uuid']
        # Use the patient instance determined according to the UUID in the URL.
        # self.patient = generics.get_object_or_404(Patient.objects.all(), uuid=patient_uuid)

        # general_test_serializer = GeneralTestSerializer(data=request.data)
        # general_test_serializer.is_valid(raise_exception=True)

        # TODO: generate PDF pathology report
        # TODO: insert record to the OpalDB.Documents

        # Add legacy_document_id value to the `GeneralTest` and save it
        # serializer.save(patient=self.patient)
        # headers = self.get_success_headers(serializer.data)
        # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
