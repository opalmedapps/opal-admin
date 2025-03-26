import urllib

from django.test import Client
from django.urls import reverse

import pytest

from .. import factories, models, tables

pytestmark = pytest.mark.django_db


def test_patienttable_mrn_render() -> None:
    """Ensure that mrn is rendered in the form `SITE: MRN` in `PatientTable`."""
    site = factories.Site(name='TEST_SITE', code='TSITE')
    patient = factories.Patient(pk=1)
    factories.HospitalPatient(pk=11, patient=patient, site=site, mrn='999999')

    patients = models.Patient.objects.filter(pk=1)
    hospital_patients = models.HospitalPatient.objects.filter(pk=11)

    patient_table = tables.PatientTable(patients)
    site_mrn = patient_table.render_mrn(hospital_patients)
    assert site_mrn == 'TSITE: 999999'


def test_relationshiptable_pending_status_render() -> None:
    """Ensure that pending status is rendered in the form `STATUS (number of days)` in `PendingRelationshipTable`."""
    relationship_record = factories.Relationship()
    relationships = models.Relationship.objects.filter()

    relationship_table = tables.PendingRelationshipTable(relationships)
    status_format = relationship_table.render_status('Pending', relationship_record)

    assert status_format == 'Pending (0 days)'


def test_relationships_table_readonly_url(relationship_user: Client) -> None:
    """Ensures Relationships action buttons use readonly url for expired status."""
    hospital_patient = factories.HospitalPatient()
    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.mandatary(),
        status=models.RelationshipStatus.EXPIRED,
    )

    form_data = {
        'card_type': 'mrn',
        'site': hospital_patient.site.id,
        'medical_number': hospital_patient.mrn,
    }

    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-pending-list'),
        QUERY_STRING=query_string,
    )

    action_column = response.context['table'].columns['actions']
    action_content = action_column.current_value

    url_link = action_column.column.extra_context
    assert url_link['urlname_update'] == ''
    assert url_link['urlname_view'] == 'patients:relationships-pending-readonly'
    assert 'fa-solid fa-fas fa-eye' in action_content


def test_relationships_table_update_url(relationship_user: Client) -> None:
    """Ensures Relationships action uses edit url for statuses other than expired."""
    hospital_patient = factories.HospitalPatient()

    factories.Relationship(
        patient=hospital_patient.patient,
        type=models.RelationshipType.objects.parent_guardian(),
        status=models.RelationshipStatus.PENDING,
    )

    form_data = {
        'card_type': 'mrn',
        'site': hospital_patient.site.id,
        'medical_number': hospital_patient.mrn,
    }

    query_string = urllib.parse.urlencode(form_data)
    response = relationship_user.get(
        path=reverse('patients:relationships-pending-list'),
        QUERY_STRING=query_string,
    )

    action_column = response.context['table'].columns['actions']
    action_content = action_column.current_value
    url_link = action_column.column.extra_context
    assert url_link['urlname_update'] == 'patients:relationships-pending-update'
    assert url_link['urlname_view'] == ''
    assert 'fa-solid fa-pencil-alt' in action_content
