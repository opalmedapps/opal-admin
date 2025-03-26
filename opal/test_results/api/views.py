"""This module provides `APIViews` for the `test-results` app REST APIs."""

from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError

from opal.core.drf_permissions import CreateModelPermissions
from opal.legacy.models import LegacyDocument
from opal.patients.models import Patient

from ..models import GeneralTest, TestType
from ..utils import generate_pathology_report
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

    @transaction.atomic
    def perform_create(self, serializer: serializers.BaseSerializer[GeneralTest]) -> None:
        """
        Perform the `GeneralTest` (a.k.a pathology) record creation for a specific patient.

        Ensures that the patient with the given UUID exists.

        Args:
            serializer: the serializer instance to use

        Raises:
            ValidationError: if new `LegacyDocument` record could not be saved to the database
        """
        # Patient for whom the pathology report is being created
        patient: Patient = get_object_or_404(
            Patient.objects.prefetch_related(
                'hospital_patients__site',
            ),
            uuid=self.kwargs['uuid'],
        )

        # Generate the pathology report
        pathology_pdf_path = generate_pathology_report(
            patient=patient,
            pathology_data=serializer.validated_data,
        )

        # Insert a record to the legacy OpalDB.Documents table to indicate a new pathology report is available
        try:
            legacy_document = LegacyDocument.objects.create_pathology_document(
                legacy_patient_id=patient.legacy_id,
                prepared_by=1,  # TODO: add LegacyStaff model; finalize find_doctor_name()
                received_at=serializer.validated_data['received_at'],
                report_file_name=pathology_pdf_path.name,
            )
        except DatabaseError as db_exp:
            # Raise `ValidationError` exception if `LegacyDocument` record could not be saved to the database
            raise ValidationError(
                '{0} {1}'.format(
                    'An error occurred while inserting `LegacyDocument` record to the database.',
                    db_exp,
                ),
            )

        # Save `GeneralTest` record to the database
        serializer.save(
            patient=patient,
            type=TestType.PATHOLOGY,
            legacy_document_id=legacy_document.documentsernum,
        )
