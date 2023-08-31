"""This module provides `APIViews` for the `test-results` app REST APIs."""
from datetime import datetime
from pathlib import Path
from typing import Any

from django.db import models
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers

from opal.core.drf_permissions import CreateModelPermissions
from opal.hospital_settings.models import Institution
from opal.patients.models import Patient
from opal.services.reports import PathologyData, ReportService

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

        # Parsed observations that contain SPCI, SPSPECI, SPGROS, and SPDX values
        observations = self._parse_observations(serializer.validated_data['observations'])

        # Note containing doctors' names and time that show by whom and when the report was created
        note_comment = self._parse_notes(serializer.validated_data['notes'])

        # Generate the pathology report
        self.report_service.generate_pathology_report(
            pathology_data=PathologyData(
                site_logo_path=Path(Institution.objects.get().logo.path),
                site_name='',  # TODO: decide what site name we should include (QSCCD-1438)
                site_building_address='',  # TODO: decide what site we should use for the address (QSCCD-1438)
                site_city='',  # TODO: decide what site we should use for the address (QSCCD-1438)
                site_province='',  # TODO: decide what site we should use for the address (QSCCD-1438)
                site_postal_code='',  # TODO: decide what site we should use for the address (QSCCD-1438)
                site_phone='',  # TODO: decide what site we should use for the address (QSCCD-1438)
                patient_first_name=patient.first_name,
                patient_last_name=patient.last_name,
                patient_date_of_birth=patient.date_of_birth,
                patient_ramq=patient.ramq if patient.ramq else '',
                patient_sites_and_mrns=patient_sites_and_mrns,
                test_number=serializer.validated_data['case_number'],  # TODO: confirm if case_number required
                test_collected_at=serializer.validated_data['collected_at'],
                test_reported_at=serializer.validated_data['reported_at'],
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

    def _parse_observations(
        self,
        observations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Parse the pathology observations and extract SPCI, SPSPECI, SPGROS, SPDX values.

        Args:
            observations: list of observation dictionaries to be parsed

        Returns:
            dictionary of the observations' SPCI, SPSPECI, SPGROS, SPDX values
        """
        parsed_observations: dict[str, Any] = {
            'SPCI': [],
            'SPSPECI': [],
            'SPGROS': [],
            'SPDX': [],
        }

        for obs in observations:
            match obs['identifier_code']:
                case 'SPCI':
                    parsed_observations['SPCI'].append(obs['value'])
                case 'SPSPECI':
                    parsed_observations['SPSPECI'].append(obs['value'])
                case 'SPGROS':
                    parsed_observations['SPGROS'].append(obs['value'])
                case 'SPDX':
                    parsed_observations['SPDX'].append(obs['value'])

        return parsed_observations

    def _parse_notes(self, notes: list[dict[str, Any]]) -> dict[str, Any]:
        """Parse the pathology notes and extract the information by whom and when the report was created.

        Args:
            notes: _description_

        Returns:
            dict[str, Any]: _description_
        """
        parsed_notes: dict[str, Any] = {
            'prepared_by': '',
            'prepared_at': datetime(1, 1, 1),
        }
        doctor_names = []
        for note in notes:
            doctor_name = self._find_doctor_name(note['note_text'])

            if doctor_name:
                doctor_names.append(doctor_name)

            # TODO: Decide what datetime to use in case of several notes (e.g., the latest vs oldest)
            prepared_at = self._find_note_date(note['note_text'])
            if prepared_at > parsed_notes['prepared_at']:
                parsed_notes['prepared_at'] = prepared_at

        parsed_notes['prepared_by'] = '; '.join(doctor_names)
        return parsed_notes

    def _find_doctor_name(self, note_text: str) -> str:
        """Find doctor's name in a pathology note.

        Args:
            note_text: a pathology note in which doctor's name should be found

        Returns:
            doctor's name found in the pathology note
        """
        # TODO: implement regex
        return ''

    def _find_note_date(self, note_text: str) -> datetime:
        """Find date and time in a pathology note that indicates when the doctor's comments were left.

        Args:
            note_text: a pathology note in which the date and time of note creation should be found

        Returns:
            date and time of note creation
        """
        # TODO: implement regex
        return datetime(1, 1, 1)
