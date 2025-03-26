"""Utility functions used by the test results app."""

from datetime import datetime
from typing import Any


def parse_observations(
    observations: list[dict[str, Any]],
) -> dict[str, list]:
    """Parse the pathology observations and extract SPCI, SPSPECI, SPGROS, SPDX values.

    Args:
        observations: list of observation dictionaries to be parsed

    Returns:
        dictionary of the observations' SPCI, SPSPECI, SPGROS, SPDX values
    """
    parsed_observations: dict[str, list] = {
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


def parse_notes(notes: list[dict[str, Any]]) -> dict[str, Any]:
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
        if 'note_text' not in note:
            continue

        doctor_name = find_doctor_name(note['note_text'])

        if doctor_name:
            doctor_names.append(doctor_name)

        # TODO: Decide what datetime to use in case of several notes (e.g., the latest vs oldest)
        prepared_at = find_note_date(note['note_text'])
        if prepared_at > parsed_notes['prepared_at']:
            parsed_notes['prepared_at'] = prepared_at

    parsed_notes['prepared_by'] = '; '.join(doctor_names)
    return parsed_notes


def find_doctor_name(note_text: str) -> str:
    """Find doctor's name in a pathology note.

    Args:
        note_text: a pathology note in which doctor's name should be found

    Returns:
        doctor's name found in the pathology note
    """
    # TODO: implement regex
    return ''


def find_note_date(note_text: str) -> datetime:
    """Find date and time in a pathology note that indicates when the doctor's comments were left.

    Args:
        note_text: a pathology note in which the date and time of note creation should be found

    Returns:
        date and time of note creation
    """
    # TODO: implement regex
    return datetime(1, 1, 1)
