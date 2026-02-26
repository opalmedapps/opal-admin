# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utility functions used by the test results app."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from opal.hospital_settings.models import Institution, Site
from opal.patients.models import Patient
from opal.services.reports.base import InstitutionData, PatientData, SiteData
from opal.services.reports.pathology import PathologyData, generate_pdf

LOGGER = logging.getLogger(__name__)


def generate_pathology_report(
    patient: Patient,
    pathology_data: dict[str, Any],
) -> Path:
    """
    Generate the pathology PDF report.

    Args:
        patient: patient instance for whom a new PDF pathology report being generated
        pathology_data: pathology data required to generate the PDF report

    Returns:
        Path: path to the generated pathology report
    """
    # Parsed observations that contain SPCI, SPSPECI, SPGROS, and SPDX values
    observations = _parse_observations(pathology_data['observations'])

    # Note containing doctors' names and time that show by whom and when the report was created
    note_comment = _parse_notes(pathology_data['notes'])

    # Find Site record filtering by receiving_facility field (a.k.a. site code)
    site = _get_site_instance(pathology_data['receiving_facility'])

    return generate_pdf(
        institution_data=InstitutionData(
            institution_logo_path=Path(Institution.objects.get().logo.path),
            # TODO: clarify where to get the value (currently set as a test document)
            document_number=settings.REPORT_DOCUMENT_NUMBER,
            source_system=settings.REPORT_SOURCE_SYSTEM,
        ),
        patient_data=PatientData(
            patient_first_name=patient.first_name,
            patient_last_name=patient.last_name,
            patient_date_of_birth=patient.date_of_birth,
            patient_ramq=patient.ramq or '',
            patient_sites_and_mrns=list(
                patient.hospital_patients
                .all()
                .annotate(
                    site_code=models.F('site__acronym'),
                )
                .values('mrn', 'site_code'),
            ),
        ),
        site_data=SiteData(
            site_name=site.name,
            site_building_address=site.street_name,
            site_city=site.city,
            site_province=site.province_code,
            site_postal_code=site.postal_code,
            site_phone=site.contact_telephone,
        ),
        pathology_data=PathologyData(
            test_number=pathology_data.get('case_number', ''),
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


def _parse_observations(
    observations: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """
    Parse the pathology observations and extract SPCI, SPSPECI, SPGROS, SPDX values.

    Args:
        observations: list of observation dictionaries to be parsed

    Returns:
        dictionary of the observations' SPCI, SPSPECI, SPGROS, SPDX values
    """
    parsed_observations: dict[str, list[str]] = {
        'SPCI': [],
        'SPSPECI': [],
        'SPGROS': [],
        'SPDX': [],
    }

    for obs in observations:
        if not set({'identifier_code', 'value'}).issubset(obs):
            continue

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


def _parse_notes(notes: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Parse the pathology notes and extract the information by whom and when the report was created.

    Args:
        notes: _description_

    Returns:
        dict[str, Any]: _description_
    """
    parsed_notes: dict[str, Any] = {
        'prepared_by': '',
        'prepared_at': datetime(1, 1, 1, tzinfo=timezone.get_current_timezone()),
    }
    doctor_names = []

    for note in notes:
        if 'note_text' not in note:
            continue

        doctor_name = _find_doctor_name(note['note_text'])

        if doctor_name:
            doctor_names.append(doctor_name)

        # TODO: Decide what datetime to use in case of several notes (e.g., the latest vs oldest)
        prepared_at = _find_note_date(note['note_text'])
        parsed_notes['prepared_at'] = max(prepared_at, parsed_notes['prepared_at'])

    parsed_notes['prepared_by'] = '; '.join(doctor_names)
    return parsed_notes


def _get_site_instance(receiving_facility: str) -> Site:
    """
    Fetch Site record by given receiving_facility code.

    If Site cannot be found, log the incident and return a Site with empty fields.

    Args:
        receiving_facility: the receiving facility code

    Returns:
        A Site instance
    """
    try:
        return Site.objects.get(acronym=receiving_facility)
    except Site.DoesNotExist:
        LOGGER.exception(
            'An error occurred during pathology report generation.'
            + f'Given receiving_facility code does not exist: {receiving_facility}.'
            + 'Proceeded generation with an empty Site.'
        )

        return Site(
            name='',
            street_name='',
            city='',
            province_code='',
            postal_code='',
            contact_telephone='',
        )


def _find_doctor_name(note_text: str) -> str:
    """
    Find doctor's name in a pathology note.

    Args:
        note_text: a pathology note in which doctor's name should be found

    Returns:
        doctor's name found in the pathology note
    """
    # Regular expression pattern
    pattern = r'Electronically signed on [\d\-A-Z]+ \d{1,2}:\d{2} [apm]{2}\\.br\\By (.+?)(?:,,|$)'
    match = re.search(pattern, note_text)

    # Extract and return doctor's full name
    return match.group(1).strip() if match else ''


def _find_note_date(note_text: str) -> datetime:
    """
    Find date and time in a pathology note that indicates when the doctor's comments were left.

    Args:
        note_text: a pathology note in which the date and time of note creation should be found

    Returns:
        date and time of note creation
    """
    pattern = r'Electronically signed on ([\d\-A-Z]+ \d{1,2}:\d{2} [apm]{2})\\.br\\By (.+?)(?:,,|$)'
    match = re.search(pattern, note_text)

    # Extract date and time of note text
    if match:
        note_date = match.group(1).strip()
        return datetime.strptime(note_date, '%d-%b-%Y %I:%M %p').astimezone(timezone.get_current_timezone())
    return datetime(1, 1, 1, tzinfo=timezone.get_current_timezone())
