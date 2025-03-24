# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime as dt
import urllib
from datetime import date, datetime, timedelta
from typing import Any

from django.test import Client
from django.urls import reverse
from django.utils import timezone

import pytest
from pytest_mock import MockerFixture

from opal.services.integration.schemas import HospitalNumberSchema, PatientSchema

from .. import constants, factories, models, tables

pytestmark = pytest.mark.django_db


def test_patienttable_render_date_of_birth_patient() -> None:
    """Ensure that the date of birth is rendered correctly for a `Patient`."""
    patient = factories.Patient.create()

    table = tables.PatientTable([])

    assert table.render_date_of_birth(patient.date_of_birth) == patient.date_of_birth


def test_patienttable_render_date_of_birth_str() -> None:
    """Ensure that the date of birth is rendered correctly for a date string."""
    table = tables.PatientTable([])

    assert table.render_date_of_birth('2020-05-08') == date(2020, 5, 8)


def test_patienttable_render_mrns_patient() -> None:
    """Ensure that MRNs are rendered in the form `SITE: MRN` in `PatientTable` for a `Patient`."""
    patient = factories.Patient.create()
    site = factories.Site.create(name='TEST_SITE', acronym='TSITE')
    site2 = factories.Site.create(name='Test2', acronym='TST2')
    factories.HospitalPatient.create(patient=patient, site=site, mrn='999999')
    factories.HospitalPatient.create(patient=patient, site=site2, mrn='1234567')

    hospital_patients = models.HospitalPatient.objects.filter(patient=patient)

    patient_table = tables.PatientTable([])
    site_mrn = patient_table.render_mrns(hospital_patients)
    assert site_mrn == 'TSITE: 999999, TST2: 1234567'


def test_patienttable_render_mrns_mrndata() -> None:
    """Ensure that MRNs are rendered correctly for MRN data."""
    mrns = [
        HospitalNumberSchema(site='RVH', mrn='9999996'),
        HospitalNumberSchema(site='MGH', mrn='1234567'),
    ]

    patient_table = tables.PatientTable([])
    site_mrn = patient_table.render_mrns(mrns)
    assert site_mrn == 'RVH: 9999996, MGH: 1234567'


def test_patienttable_render_mrns_dict() -> None:
    """Ensure that MRNs are rendered correctly for a dictionary of MRN data."""
    mrns = [
        {'site': 'RVH', 'mrn': '9999996', 'active': True},
        {'site': 'MGH', 'mrn': '1234567', 'active': True},
    ]

    patient_table = tables.PatientTable([])
    site_mrn = patient_table.render_mrns(mrns)
    assert site_mrn == 'RVH: 9999996, MGH: 1234567'


def test_patienttable_render_health_insurance_number() -> None:
    """Ensure that the health insurance number/RAMQ is rendered correctly."""
    data: dict[str, Any] = {
        'first_name': 'Homer',
        'last_name': 'Simpson',
        'sex': 'male',
        'date_of_birth': '1986-10-05',
        'health_insurance_number': 'SIMM86600599',
        'date_of_death': None,
        'mrns': [],
    }

    patient_table = tables.PatientTable([
        PatientSchema.model_validate(data),
        factories.Patient.create(ramq='TEST'),
    ])

    row1 = patient_table.rows[0]
    row2 = patient_table.rows[1]

    assert row1.get_cell_value('health_insurance_number') == 'SIMM86600599'
    assert row2.get_cell_value('health_insurance_number') == 'TEST'


def _mock_datetime(mocker: MockerFixture) -> None:
    # mock the current timezone to avoid flaky tests
    current_time = datetime(2022, 6, 2, 2, 0, tzinfo=dt.timezone.utc)
    mocker.patch.object(timezone, 'now', return_value=current_time)


def test_relationshiptable_pending_status_render_singular(mocker: MockerFixture) -> None:
    """Ensure that pending status is rendered in the form `STATUS (number of days)` in singular form."""
    _mock_datetime(mocker)

    # in case of `zero` number of days
    today_date = date(2022, 6, 2)
    relationship_record = factories.Relationship.create(request_date=today_date)
    relationships = models.Relationship.objects.filter()

    relationship_table = tables.PendingRelationshipTable(relationships)
    status_format = relationship_table.render_status('Pending', relationship_record)

    assert status_format == 'Pending (0 days)'

    # in case of `one` number of days
    today_date = date(2022, 6, 1)
    relationship_record = factories.Relationship.create(request_date=today_date)
    relationships = models.Relationship.objects.filter()

    relationship_table = tables.PendingRelationshipTable(relationships)
    status_format = relationship_table.render_status('Pending', relationship_record)

    assert status_format == 'Pending (1 day)'


def test_relationshiptable_pending_status_render_plural(mocker: MockerFixture) -> None:
    """Ensure that pending status is rendered in the form `STATUS (number of days)` in plural form."""
    _mock_datetime(mocker)

    today_date = date(2022, 6, 2) - timedelta(days=5)
    relationship_record = factories.Relationship.create(request_date=today_date)
    relationships = models.Relationship.objects.filter()

    relationship_table = tables.PendingRelationshipTable(relationships)
    status_format = relationship_table.render_status('Pending', relationship_record)

    assert status_format == 'Pending (5 days)'


def test_relationships_table_readonly_url(relationship_user: Client) -> None:
    """Ensures Relationships action buttons use readonly url for expired status."""
    hospital_patient = factories.HospitalPatient.create()
    factories.Relationship.create(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.mandatary(),
        status=models.RelationshipStatus.EXPIRED,
    )

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': hospital_patient.mrn,
    }

    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-list'),
        QUERY_STRING=query_string,
    )

    action_column = response.context['table'].columns['actions']
    action_content = action_column.current_value

    url_link = action_column.column.extra_context
    assert url_link['urlname_update'] == ''
    assert url_link['urlname_view'] == 'patients:relationships-view-update'
    assert 'fa-solid fa-fas fa-eye' in action_content


def test_relationships_table_update_url(relationship_user: Client) -> None:
    """Ensures Relationships action uses edit url for statuses other than expired."""
    hospital_patient = factories.HospitalPatient.create()

    factories.Relationship.create(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.parent_guardian(),
        status=models.RelationshipStatus.PENDING,
    )

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': hospital_patient.mrn,
    }

    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-list'),
        QUERY_STRING=query_string,
    )

    action_column = response.context['table'].columns['actions']
    action_content = action_column.current_value
    url_link = action_column.column.extra_context
    assert url_link['urlname_update'] == 'patients:relationships-view-update'
    assert url_link['urlname_view'] == ''
    assert 'fa-solid fa-pencil-alt' in action_content
