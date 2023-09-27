"""This module provides `APIViews` for the `test-results` app REST APIs."""

from pathlib import Path

from django.db import models
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers

from opal.core.drf_permissions import CreateModelPermissions
from opal.hospital_settings.models import Institution
from opal.patients.models import Patient
from opal.services.reports import PathologyData, ReportService

from ..models import GeneralTest, TestType
from ..utils import parse_notes, parse_observations
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
    # Report service for generating pathology reports
    report_service = ReportService()

    def perform_create(self, serializer: serializers.BaseSerializer[GeneralTest]) -> None:
        """
        Perform the `GeneralTest` (a.k.a pathology) record creation for a specific patient.

        Ensures that the patient with the given UUID exists.

        Args:
            serializer: the serializer instance to use
        """
        # Patient for whom the pathology report is being created
        patient: Patient = get_object_or_404(
            Patient.objects.prefetch_related(
                'hospital_patients__site',
            ),
            uuid=self.kwargs['uuid'],
        )

        patient_sites_and_mrns = list(
            patient.hospital_patients.all().annotate(
                site_code=models.F('site__code'),
            ).values('mrn', 'site_code'),
        )

        # Validate pathology data
        pathology_data = serializer.validated_data

        # Parsed observations that contain SPCI, SPSPECI, SPGROS, and SPDX values
        observations = parse_observations(pathology_data['observations'])

        # Note containing doctors' names and time that show by whom and when the report was created
        note_comment = parse_notes(pathology_data['notes'])

        # Generate the pathology report
        self.report_service.generate_pathology_report(
            pathology_data=PathologyData(
                site_logo_path=Path(Institution.objects.get().logo.path),
                site_name='',  # TODO: decide what site name we should include (QSCCD-1438)
                site_building_address='',  # TODO: decide what site name we should include (QSCCD-1438)
                site_city='',  # TODO: decide what site name we should include (QSCCD-1438)
                site_province='',  # TODO: decide what site name we should include (QSCCD-1438)
                site_postal_code='',  # TODO: decide what site name we should include (QSCCD-1438)
                site_phone='',  # TODO: decide what site name we should include (QSCCD-1438)
                patient_first_name=patient.first_name,
                patient_last_name=patient.last_name,
                patient_date_of_birth=patient.date_of_birth,
                patient_ramq=patient.ramq if patient.ramq else '',
                patient_sites_and_mrns=patient_sites_and_mrns,
                test_number=pathology_data['case_number'] if 'case_number' in pathology_data else '',
                test_collected_at=pathology_data['collected_at'],
                test_reported_at=pathology_data['reported_at'],
                observation_clinical_info=observations['SPCI'],
                observation_specimens=observations['SPSPECI'],
                observation_descriptions=observations['SPGROS'],
                observation_diagnosis=observations['SPDX'],
                prepared_by=note_comment['prepared_by'],
                prepared_at=note_comment['prepared_at'],
            ),
        )

        # TODO: Insert record to the OpalDB.Documents

        # TODO: Use DocumentSerNum field of the OpalDB.Documents table as legacy_document_id
        serializer.save(
            patient=patient,
            type=TestType.PATHOLOGY,
            legacy_document_id=1,
        )
