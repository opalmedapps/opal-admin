"""This module provides `APIViews` for the `test-results` app REST APIs."""
from rest_framework import generics, serializers

from opal.core.drf_permissions import CreateModelPermissions

from ..models import GeneralTest
from .serializers import PathologySerializer


class CreatePathologyView(generics.CreateAPIView):
    """
    `CreateAPIView` for handling POST requests for the `GeneralTest` and creating pathology reports.

    Supports the creation of one or more instances of the nested `observations` and `notes` records.
    """

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
        # TODO: Add legacy_document_id value to the `GeneralTest` instance
        # TODO: Run serializer.validate() due to added legacy_document_id field? (TBD)

        serializer.save()
