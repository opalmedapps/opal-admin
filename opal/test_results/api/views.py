"""This module provides `APIViews` for the `test-results` app REST APIs."""
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers

from opal.core.drf_permissions import CreateModelPermissions
from opal.patients.models import Patient

from ..models import GeneralTest, TestType
from .serializers import PathologySerializer


class CreatePathologyView(generics.CreateAPIView):
    """
    `CreateAPIView` for handling POST requests for the `GeneralTest` and creating pathology reports.

    Supports the creation of one or more instances of the nested `observations` and `notes` records.
    """

    # DjangoModelPermission requires a queryset to determine the model
    queryset = GeneralTest.objects.none()
    serializer_class = PathologySerializer
    permission_classes = [CreateModelPermissions]
    pagination_class = None

    def perform_create(self, serializer: serializers.BaseSerializer[GeneralTest]) -> None:
        """
        Perform the `GeneralTest` (a.k.a pathology) record creation for a specific patient.

        Ensures that the patient with the given UUID exists.

        Args:
            serializer: the serializer instance to use
        """
        # TODO: Generate PDF pathology report
        # TODO: Insert record to the OpalDB.Documents

        # TODO: Use DocumentSerNum field of the OpalDB.Documents table as legacy_document_id
        serializer.save(
            patient=get_object_or_404(Patient, uuid=self.kwargs['uuid']),
            type=TestType.PATHOLOGY,
            legacy_document_id=1,
        )
