# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime as dt
from pathlib import Path
from typing import Any

from django.db import models
from django.utils import timezone

import pandas as pd
import pytest
import pytz
from pytest_django.asserts import assertRaisesMessage

from opal.caregivers import factories as caregiver_factories
from opal.legacy import factories as legacy_factories
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.usage_statistics import factories as stats_factories
from opal.usage_statistics import models as stats_models
from opal.usage_statistics import utils as stats_utils

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_empty_relationship_mapping() -> None:
    """Ensure RelationshipMapping can be initialized with no relationships without errors."""
    annotated_relationships = _fetch_annotated_relationships()
    relationships_dict = stats_utils.RelationshipMapping(annotated_relationships)

    assert not relationships_dict


def test_relationship_mapping_with_multiple_usernames() -> None:
    """Ensure RelationshipMapping successfully creates relationships mapping with multiple usernames."""
    marge_caregiver = caregiver_factories.CaregiverProfile.create(
        user=caregiver_factories.Caregiver.create(username='marge'),
        legacy_id=1,
    )
    homer_caregiver = caregiver_factories.CaregiverProfile.create(
        user=caregiver_factories.Caregiver.create(username='homer'),
        legacy_id=2,
    )
    patient_factories.Relationship.create(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=patient_factories.Patient.create(legacy_id=51, ramq='TEST01161972'),
        caregiver=marge_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    homer_patient = patient_factories.Patient.create(legacy_id=52, ramq='TEST01161973')
    patient_factories.Relationship.create(
        type=patient_models.RelationshipType.objects.guardian_caregiver(),
        patient=homer_patient,
        caregiver=marge_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    patient_factories.Relationship.create(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=homer_patient,
        caregiver=homer_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )

    annotated_relationships = _fetch_annotated_relationships()
    relationships_dict = stats_utils.RelationshipMapping(annotated_relationships)

    assert relationships_dict


def test_aggregated_patient_received_data_with_no_statistics() -> None:
    """Ensure that get_aggregated_patient_received_data function does not fail when there is no statistics."""
    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    assert (
        stats_utils.get_aggregated_patient_received_data(
            start_datetime_period,
            end_datetime_period,
        ).count()
        == 0
    )


def test_aggregated_patient_received_data_previous_day() -> None:
    """Ensure that get_aggregated_patient_received_data returns patients' received data for the previous day."""
    patient = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=patient)
    previous_day = timezone.now() - dt.timedelta(days=1)

    legacy_factories.LegacyAppointmentFactory.create(
        date_added=timezone.now() - dt.timedelta(days=3),
        scheduledstarttime=timezone.now() - dt.timedelta(days=2),
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        date_added=timezone.now() - dt.timedelta(days=2),
        scheduledstarttime=previous_day,
        checkin=0,
    )
    next_appointment = timezone.now()
    legacy_factories.LegacyAppointmentFactory.create(
        date_added=timezone.now() - dt.timedelta(days=1),
        scheduledstarttime=next_appointment,
        state='Active',
        status='Open',
    )

    legacy_factories.LegacyDocumentFactory.create(
        patientsernum=patient,
        dateadded=previous_day,
    )

    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=patient,
        date_added=previous_day,
    )

    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=patient,
        date_added=previous_day,
    )

    # current day records should not be included to the final queryset
    legacy_factories.LegacyAppointmentFactory.create(
        date_added=timezone.now(),
        scheduledstarttime=timezone.now() + dt.timedelta(days=1),
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 1
    assert received_data.filter(patient=patient)[0]['last_appointment_received'] == previous_day
    assert received_data.filter(patient=patient)[0]['next_appointment'] == next_appointment
    assert received_data.filter(patient=patient)[0]['appointments_received'] == 1
    assert received_data.filter(patient=patient)[0]['last_document_received'] == previous_day
    assert received_data.filter(patient=patient)[0]['documents_received'] == 1
    assert received_data.filter(patient=patient)[0]['last_educational_material_received'] == previous_day
    assert not received_data.filter(patient=patient)[0]['last_questionnaire_received']
    assert received_data.filter(patient=patient)[0]['questionnaires_received'] == 0
    assert received_data.filter(patient=patient)[0]['last_lab_received'] == previous_day
    assert received_data.filter(patient=patient)[0]['labs_received'] == 1


def test_aggregated_patient_received_data_current_day() -> None:
    """Ensure that get_aggregated_patient_received_data returns patients' received data for the current day."""
    patient = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=patient)
    current_day = timezone.now()

    legacy_factories.LegacyAppointmentFactory.create(
        date_added=timezone.now() - dt.timedelta(days=3),
        scheduledstarttime=timezone.now() - dt.timedelta(days=2),
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        date_added=current_day,
        scheduledstarttime=timezone.now() + dt.timedelta(days=2),
        checkin=0,
    )
    legacy_factories.LegacyAppointmentFactory.create(
        date_added=timezone.now() - dt.timedelta(days=1),
        scheduledstarttime=current_day,
        state='Active',
        status='Open',
    )

    legacy_factories.LegacyDocumentFactory.create(
        patientsernum=patient,
        dateadded=current_day,
    )

    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=patient,
        date_added=current_day,
    )

    # previous day records should not be included to the final queryset
    next_appointment = current_day + dt.timedelta(days=1)
    legacy_factories.LegacyAppointmentFactory.create(
        date_added=timezone.now() - dt.timedelta(days=1),
        scheduledstarttime=next_appointment,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=patient,
        date_added=current_day - dt.timedelta(days=1),
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now(),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    previous_day = current_day - dt.timedelta(days=1)

    assert received_data.count() == 1
    assert received_data.filter(patient=patient)[0]['last_appointment_received'] == current_day
    assert received_data.filter(patient=patient)[0]['next_appointment'] == next_appointment
    assert received_data.filter(patient=patient)[0]['appointments_received'] == 1
    assert received_data.filter(patient=patient)[0]['last_document_received'] == current_day
    assert received_data.filter(patient=patient)[0]['documents_received'] == 1
    assert received_data.filter(patient=patient)[0]['last_educational_material_received'] == current_day
    assert received_data.filter(patient=patient)[0]['last_questionnaire_received'] == previous_day
    assert received_data.filter(patient=patient)[0]['questionnaires_received'] == 0
    assert not received_data.filter(patient=patient)[0]['last_lab_received']
    assert received_data.filter(patient=patient)[0]['labs_received'] == 0


def test_aggregated_patient_received_data_last_appointment_statistics() -> None:
    """Ensure that get_aggregated_patient_received_data correctly aggregates last appointment statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()
    next_day = timezone.now() + dt.timedelta(days=1)

    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        scheduledstarttime=previous_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=previous_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        scheduledstarttime=current_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=current_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        scheduledstarttime=next_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=next_day,
        status='Completed',
        state='Closed',
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['last_appointment_received'] == previous_day
    assert received_data.filter(patient=homer)[0]['last_appointment_received'] == previous_day


def test_aggregated_patient_received_data_next_appointment_statistics() -> None:
    """Ensure that get_aggregated_patient_received_data correctly aggregates next appointment statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    current_day = timezone.now()
    next_day = timezone.now() + dt.timedelta(days=1)

    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        scheduledstarttime=current_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=current_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        scheduledstarttime=next_day,
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=next_day,
        status='Completed',
        state='Closed',
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        scheduledstarttime=next_day + dt.timedelta(days=1),
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=next_day + dt.timedelta(days=1),
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    homer_next_appointment_date = next_day + dt.timedelta(days=1)
    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['next_appointment'] == next_day
    assert received_data.filter(patient=homer)[0]['next_appointment'] == homer_next_appointment_date


def test_aggregated_patient_received_data_received_appointments_statistics() -> None:
    """Ensure that get_aggregated_patient_received_data correctly aggregates received appointments statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()
    next_day = timezone.now() + dt.timedelta(days=1)

    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        date_added=previous_day,
    )

    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=current_day,
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=marge,
        scheduledstarttime=next_day,
    )
    legacy_factories.LegacyAppointmentFactory.create(
        patientsernum=homer,
        scheduledstarttime=next_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['appointments_received'] == 2
    assert received_data.filter(patient=homer)[0]['appointments_received'] == 1


def test_aggregated_patient_received_data_last_document_statistics() -> None:
    """Ensure that get_aggregated_patient_received_data correctly aggregates last document statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()
    next_day = timezone.now() + dt.timedelta(days=1)
    homer_last_document_date = previous_day - dt.timedelta(days=1)

    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=1,
        patientsernum=marge,
        dateadded=previous_day,
    )
    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=2,
        patientsernum=homer,
        dateadded=homer_last_document_date,
    )

    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=3,
        patientsernum=marge,
        dateadded=current_day,
    )
    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=4,
        patientsernum=homer,
        dateadded=current_day,
    )

    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=5,
        patientsernum=marge,
        dateadded=next_day,
    )
    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=6,
        patientsernum=homer,
        dateadded=next_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['last_document_received'] == previous_day
    assert received_data.filter(patient=homer)[0]['last_document_received'] == homer_last_document_date


def test_aggregated_patient_received_data_received_documents_statistics() -> None:
    """Ensure that get_aggregated_patient_received_data correctly aggregates received documents statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()
    next_day = timezone.now() + dt.timedelta(days=1)

    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=1,
        patientsernum=marge,
        dateadded=previous_day,
    )
    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=2,
        patientsernum=homer,
        dateadded=previous_day,
    )
    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=3,
        patientsernum=homer,
        dateadded=previous_day,
    )

    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=4,
        patientsernum=marge,
        dateadded=current_day,
    )

    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=5,
        patientsernum=marge,
        dateadded=next_day,
    )
    legacy_factories.LegacyDocumentFactory.create(
        documentsernum=6,
        patientsernum=homer,
        dateadded=next_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['documents_received'] == 1
    assert received_data.filter(patient=homer)[0]['documents_received'] == 2


def test_aggregated_patient_received_data_last_educational_material_statistics() -> None:
    """Ensure get_aggregated_patient_received_data correctly aggregates last educational material statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    two_days_ago = timezone.now() - dt.timedelta(days=2)
    three_days_ago = timezone.now() - dt.timedelta(days=3)
    current_day = timezone.now()

    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=marge,
        date_added=two_days_ago,
    )
    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=homer,
        date_added=two_days_ago,
    )

    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=marge,
        date_added=three_days_ago,
    )
    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=homer,
        date_added=three_days_ago,
    )

    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=marge,
        date_added=current_day,
    )
    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=homer,
        date_added=current_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['last_educational_material_received'] == two_days_ago
    assert received_data.filter(patient=homer)[0]['last_educational_material_received'] == two_days_ago


def test_aggregated_patient_received_data_received_edu_materials_statistics() -> None:
    """Ensure get_aggregated_patient_received_data correctly aggregates received edu materials statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()

    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=homer,
        date_added=previous_day,
    )
    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=homer,
        date_added=previous_day,
    )

    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=marge,
        date_added=current_day,
    )
    legacy_factories.LegacyEducationalMaterialFactory.create(
        patientsernum=homer,
        date_added=current_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['educational_materials_received'] == 2
    assert received_data.filter(patient=homer)[0]['educational_materials_received'] == 2


def test_aggregated_patient_received_data_last_questionnaire_statistics() -> None:
    """Ensure get_aggregated_patient_received_data correctly aggregates last questionnaire statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    two_days_ago = timezone.now() - dt.timedelta(days=2)
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()

    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=marge,
        date_added=two_days_ago,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=homer,
        date_added=two_days_ago,
    )

    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=marge,
        date_added=current_day,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=homer,
        date_added=current_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['last_questionnaire_received'] == previous_day
    assert received_data.filter(patient=homer)[0]['last_questionnaire_received'] == two_days_ago


def test_aggregated_patient_received_data_received_questionnaire_statistics() -> None:
    """Ensure get_aggregated_patient_received_data correctly aggregates received questionnaire statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()

    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=homer,
        date_added=previous_day,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=homer,
        date_added=previous_day,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=homer,
        date_added=previous_day,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=marge,
        date_added=previous_day,
    )

    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=marge,
        date_added=current_day,
    )
    legacy_factories.LegacyQuestionnaireFactory.create(
        patientsernum=homer,
        date_added=current_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['questionnaires_received'] == 1
    assert received_data.filter(patient=homer)[0]['questionnaires_received'] == 3


def test_aggregated_patient_received_data_last_lab_statistics() -> None:
    """Ensure get_aggregated_patient_received_data correctly aggregates last lab statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)
    current_day = timezone.now()

    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=marge,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=marge,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=marge,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=homer,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=homer,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=homer,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now(),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert (
        received_data.filter(
            patient=marge,
        )[0]['last_lab_received'].date()
        == current_day.date()
    )
    assert (
        received_data.filter(
            patient=homer,
        )[0]['last_lab_received'].date()
        == current_day.date()
    )


def test_aggregated_patient_received_data_received_lab_statistics() -> None:
    """Ensure get_aggregated_patient_received_data correctly aggregates received lab statistics."""
    marge = legacy_factories.LegacyPatientFactory.create()
    legacy_factories.LegacyPatientControlFactory.create(patient=marge)
    homer = legacy_factories.LegacyPatientFactory.create(
        patientsernum=52,
        first_name='Homer',
        email='homer@simpson.com',
    )
    previous_day = timezone.now() - dt.timedelta(days=1)
    current_day = timezone.now()
    legacy_factories.LegacyPatientControlFactory.create(patient=homer)

    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=marge,
        date_added=previous_day,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=homer,
        date_added=previous_day,
    )

    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=marge,
        date_added=current_day,
    )
    legacy_factories.LegacyPatientTestResultFactory.create(
        patient_ser_num=homer,
        date_added=current_day,
    )

    start_datetime_period = dt.datetime.combine(
        timezone.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        tzinfo=timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        tzinfo=timezone.get_current_timezone(),
    )

    received_data = stats_utils.get_aggregated_patient_received_data(
        start_datetime_period,
        end_datetime_period,
    )

    assert received_data.count() == 2
    assert received_data.filter(patient=marge)[0]['labs_received'] == 3
    assert received_data.filter(patient=homer)[0]['labs_received'] == 1


def _fetch_annotated_relationships() -> models.QuerySet[patient_models.Relationship, dict[str, Any]]:
    """
    Fetch annotated relationships queryset used in the `RelationshipMapping`.

    Returns:
        annotated relationships queryset
    """
    date_time = timezone.now()
    relationships_queryset = patient_models.Relationship.objects.all()
    return (
        relationships_queryset.select_related(
            'patient',
            'caregiver__user',
        )
        .filter(
            models.Q(end_date__gte=date_time)
            | models.Q(end_date=None)
            | models.Q(status=patient_models.RelationshipStatus.CONFIRMED),
        )
        .exclude(
            models.Q(status=patient_models.RelationshipStatus.PENDING)
            | models.Q(status=patient_models.RelationshipStatus.DENIED),
        )
        .values(
            'patient__legacy_id',
            'patient__id',
            'caregiver__user__username',
            'caregiver__user__id',
            'id',
        )
        .annotate(
            end_date=models.Max('end_date'),
        )
    )


def test_export_data_empty_data(tmp_path: Path) -> None:
    """Ensure the export function handle the empty list."""
    file_path = tmp_path / 'test.random'
    expected_message = 'Invalid input, unable to export empty data'
    with assertRaisesMessage(
        ValueError,
        expected_message,
    ):
        stats_utils.export_data([], file_path)


def test_export_data_simple_dictionary(tmp_path: Path) -> None:
    """Ensure the export function handle the input in form of dictionary."""
    file_path = tmp_path / 'test_dict.csv'
    stats_factories.DailyUserPatientActivity.create(
        action_by_user=caregiver_factories.Caregiver.create(username='marge'),
    )
    query = stats_models.DailyUserPatientActivity.objects.all()
    model_name = query.model
    model_fields = [field.name for field in model_name._meta.get_fields()]
    data_set = list(query.values(*model_fields))
    assert not file_path.is_file()
    stats_utils.export_data(dict(data_set[0]), file_path)
    assert file_path.is_file()
    assert model_fields == list(
        pd.read_csv(file_path).head(),
    )


def test_export_data_csv(tmp_path: Path) -> None:
    """Ensure the export function generate csv file with model queryset."""
    file_path = tmp_path / 'test.csv'
    stats_factories.DailyUserPatientActivity.create(
        action_by_user=caregiver_factories.Caregiver.create(username='marge'),
    )
    query = stats_models.DailyUserPatientActivity.objects.all()
    model_name = query.model
    model_fields = [field.name for field in model_name._meta.get_fields()]
    data_set = query.values(*model_fields)
    assert not file_path.is_file()
    stats_utils.export_data(list(data_set), file_path)
    assert file_path.is_file()
    assert model_fields == list(
        pd.read_csv(file_path).head(),
    )


def test_export_data_xlsx(tmp_path: Path) -> None:
    """Ensure the export_data generate excel file with model queryset."""
    file_path = tmp_path / 'test.xlsx'
    stats_factories.DailyPatientDataReceived.create(
        patient=patient_factories.Patient.create(legacy_id=51, ramq='TEST01161972'),
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        action_date=timezone.now().date(),
    )
    query = stats_models.DailyPatientDataReceived.objects.all()
    model_name = query.model
    model_fields = [field.name for field in model_name._meta.get_fields()]
    data_set = query.values(*model_fields)
    assert not file_path.is_file()
    stats_utils.export_data(list(data_set), file_path)
    assert file_path.is_file()
    assert model_fields == list(
        pd.read_excel(file_path, nrows=1, engine='openpyxl').columns,
    )


def test_export_data_invalid_file_name(tmp_path: Path) -> None:
    """Ensure the export_data handle the invalid file format."""
    file_path = tmp_path / 'test.random'
    stats_factories.DailyUserPatientActivity.create(
        action_by_user=caregiver_factories.Caregiver.create(username='marge'),
    )
    query = stats_models.DailyUserPatientActivity.objects.all()
    model_name = query.model
    model_fields = [field.name for field in model_name._meta.get_fields()]
    data_set = query.values(*model_fields)
    expected_message = 'Invalid file format, please use either csv or xlsx'
    with assertRaisesMessage(
        ValueError,
        expected_message,
    ):
        stats_utils.export_data(list(data_set), file_path)


def test_convert_to_naive() -> None:
    """Ensure that datetime conversion function remove the timezone information."""
    sample_datetime = pd.Timestamp(dt.datetime.now(pytz.utc))
    assert sample_datetime.tz
    sample_datetime = stats_utils._convert_to_naive(sample_datetime)
    assert not sample_datetime.tz
