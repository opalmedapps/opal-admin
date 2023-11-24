from datetime import datetime
from typing import Any

import pytest
from _pytest.logging import LogCaptureFixture  # noqa: WPS436
from pytest_mock.plugin import MockerFixture

from opal.hospital_settings import factories as hospital_settings_factories
from opal.hospital_settings.models import Site

from ..utils import (  # noqa: WPS450
    _find_doctor_name,
    _find_note_date,
    _get_site_instance,
    _parse_notes,
    _parse_observations,
)

pytestmark = pytest.mark.django_db


def _create_empty_parsed_observations() -> dict[str, list]:
    """Create empty parsed observations dictionary with SPCI, SPSPECI, SPGROS, SPDX fields.

    Returns:
        parsed observations dictionary
    """
    return {
        'SPCI': [],
        'SPSPECI': [],
        'SPGROS': [],
        'SPDX': [],
    }


def _create_empty_parsed_notes() -> dict[str, Any]:
    """Create empty parsed notes dictionary with prepared_by and prepared_at fields.

    Returns:
        parsed notes dictionary
    """
    return {
        'prepared_by': '',
        'prepared_at': datetime(1, 1, 1),
    }


# tuple with note text and corresponding doctor names
test_note_text_data: list[tuple[str, str]] = [
    (r'Electronically signed on 18-OCT-2023 02:29 pm\.br\By ', 'Gertruda Evaristo, MD, MSc, FRCPC'),
    (r'Electronically signed on 18-OCT-2023 02:29 pm\.br\By ', 'Timothy John Berners-Lee, MD'),
    (r'Electronically signed on 18-OCT-2023 02:29 pm\.br\By ', 'Leonardo di ser Piero da Vinci'),
    (r'Electronically signed on 18-OCT-2023 02:29 pm\.br\By ', 'Guillaume Levasseur de Beauplan, MD, FRCPC'),
]


@pytest.mark.parametrize(('text', 'name'), test_note_text_data)
def test_find_doctor_name_success(text: str, name: str) -> None:
    """Ensure find_doctor() successfully finds doctor name in a string."""
    note_text = text + name
    assert _find_doctor_name(note_text) == name


def test_find_doctor_name_fail() -> None:
    """Ensure find_doctor() does not find doctor name and return a empty string."""
    note_text = 'AH /AH /AH'
    assert _find_doctor_name(note_text) == ''


def test_find_note_date_success() -> None:
    """Ensure find_note_date() successfully finds date and time of doctor's comment/note."""
    # TODO: update the unit test once _find_note_date() is finalized
    assert _find_note_date('Lorem ipsum dolor sit amet...') == datetime(1, 1, 1)


def test_parse_notes_with_empty_array() -> None:
    """Ensure that parse_notes() does not fail with no notes provided."""
    parsed_notes = _parse_notes([])
    assert parsed_notes == _create_empty_parsed_notes()


def test_parse_notes_with_no_note_text() -> None:
    """Ensure that parse_notes() does not fail with no note_text field provided."""
    parsed_notes = _parse_notes([
        {
            'note_source': 'test',
            'updated_at': '2023-08-31T16:03:25.805971-04:00',
        },
    ])
    assert parsed_notes == _create_empty_parsed_notes()


def test_parse_notes_success(mocker: MockerFixture) -> None:
    """Ensure that parse_notes() successfully parses notes list of dictionaries."""
    # TODO: update the unit test once _parse_notes() is finalized
    prepared_at = datetime.now()
    mocker.patch(
        'opal.test_results.utils._find_doctor_name',
        return_value='Atilla Omeroglu, MD',
    )
    mocker.patch(
        'opal.test_results.utils._find_note_date',
        return_value=prepared_at,
    )

    parsed_notes = _parse_notes([
        {
            'note_source': 'test_1',
            'note_text': 'test_1',
            'updated_at': '2023-08-31T16:03:25.805971-04:00',
        },
        {
            'note_source': 'test_2',
            'note_text': 'test_2',
            'updated_at': '2023-09-01T17:03:25.805971-04:00',
        },
    ])
    assert parsed_notes == {
        'prepared_by': 'Atilla Omeroglu, MD; Atilla Omeroglu, MD',
        'prepared_at': prepared_at,
    }


def test_parse_observations_with_empty_array() -> None:
    """Ensure that _parse_observations() does not fail with no observations provided."""
    parsed_observations = _parse_observations([])
    assert parsed_observations == _create_empty_parsed_observations()


def test_parse_observations_with_no_identifier_code() -> None:
    """Ensure that parse_observations() does not fail with no identifier_code provided."""
    parsed_observations = _parse_observations([
        {
            'identifier_text': 'identifier_text_1',
            'value': 'value_1',
        },
        {
            'identifier_text': 'identifier_text_2',
            'value': 'value_2',
        },
    ])
    assert parsed_observations == _create_empty_parsed_observations()


def test_parse_observations_with_no_value() -> None:
    """Ensure that parse_observations() does not fail with no value field provided."""
    parsed_observations = _parse_observations([
        {
            'identifier_code': 'SPCI',
            'identifier_text': 'identifier_text_1',
        },
        {
            'identifier_code': 'SPSPECI',
            'identifier_text': 'identifier_text_2',
        },
    ])
    assert parsed_observations == _create_empty_parsed_observations()


def test_parse_observations_success() -> None:
    """Ensure that parse_observations() successfully parses observations list of dictionaries."""
    parsed_observations = _parse_observations([
        {
            'identifier_code': 'SPCI',
            'identifier_text': 'identifier_text_1',
            'value': 'value_1',
            'value_units': '',
            'value_min_range': None,
            'value_max_range': None,
            'value_abnormal': 'N',
            'observed_at': '1986-10-01T12:30:30-04:00',
            'updated_at': '2023-08-31T16:03:25.805487-04:00',
        },
        {
            'identifier_code': 'SPSPECI',
            'identifier_text': 'identifier_text_2',
            'value': 'value_2',
            'value_units': '',
            'value_min_range': None,
            'value_max_range': None,
            'value_abnormal': 'N',
            'observed_at': '1986-11-01T13:30:30-04:00',
            'updated_at': '2023-09-31T17:03:25.805487-04:00',
        },
        {
            'identifier_code': 'SPGROS',
            'identifier_text': 'identifier_text_3',
            'value': 'value_3',
            'value_units': '',
            'value_min_range': None,
            'value_max_range': None,
            'value_abnormal': 'N',
            'observed_at': '1986-12-01T11:30:30-04:00',
            'updated_at': '2023-10-31T15:03:25.805487-04:00',
        },
        {
            'identifier_code': 'SPDX',
            'identifier_text': 'identifier_text_4',
            'value': 'value_4',
            'value_units': '',
            'value_min_range': None,
            'value_max_range': None,
            'value_abnormal': 'N',
            'observed_at': '1986-08-01T10:30:30-04:00',
            'updated_at': '2023-06-31T14:03:25.805487-04:00',
        },
    ])
    assert parsed_observations == {
        'SPCI': ['value_1'],
        'SPSPECI': ['value_2'],
        'SPGROS': ['value_3'],
        'SPDX': ['value_4'],
    }


def test_get_site_instance_success() -> None:
    """Ensure that _get_site_instance() successfully return Site instance."""
    hospital_settings_factories.Site(code='RVH')
    site = _get_site_instance(receiving_facility='RVH')

    assert Site.objects.filter(pk=site.pk).exists()


def test_get_site_instance_failed(caplog: LogCaptureFixture) -> None:
    """Ensure that _get_site_instance() returns an empty Site for non-existent receiving facility."""
    hospital_settings_factories.Site(code='RVH')
    receiving_facility = ''
    error = (
        'An error occurred during pathology report generation.'
        + 'Given receiving_facility code does not exist: {0}.'
        + 'Proceeded generation with an empty Site.'
    ).format(receiving_facility)
    site = _get_site_instance(receiving_facility=receiving_facility)
    assert caplog.records[0].message == error
    assert caplog.records[0].levelname == 'ERROR'
    assert site.name == ''
    assert site.street_name == ''
    assert site.city == ''
    assert site.province_code == ''
    assert site.postal_code == ''
    assert site.contact_telephone == ''
