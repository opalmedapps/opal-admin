import datetime as dt
from typing import Any

from django.utils import timezone

import pytest
from pytest_mock import MockerFixture

from opal.caregivers import factories as caregiver_factories
from opal.caregivers import models as caregiver_models
from opal.legacy import factories as legacy_factories
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.usage_statistics import factories as stats_factories
from opal.usage_statistics import models as stats_models
from opal.usage_statistics import queries as stats_queries

pytestmark = pytest.mark.django_db(databases=['default'])


def test_empty_fetch_registration_summary() -> None:
    """Ensure fetch_registration_summary() query can return an empty result without errors."""
    registration_summary = stats_queries.fetch_registration_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert registration_summary == {
        'uncompleted_registration': 0,
        'completed_registration': 0,
    }


def test_fetch_registration_summary(mocker: MockerFixture) -> None:
    """Ensure fetch_registration_summary() query successfully returns registration statistics."""
    marge_caregiver = caregiver_factories.CaregiverProfile(
        user=caregiver_factories.Caregiver(username='marge'),
        legacy_id=1,
    )
    homer_caregiver = caregiver_factories.CaregiverProfile(
        user=caregiver_factories.Caregiver(username='homer'),
        legacy_id=2,
    )
    bart_caregiver = caregiver_factories.CaregiverProfile(
        user=caregiver_factories.Caregiver(username='bart'),
        legacy_id=3,
    )
    lisa_caregiver = caregiver_factories.CaregiverProfile(
        user=caregiver_factories.Caregiver(username='lisa'),
        legacy_id=4,
    )
    homer_patient = patient_factories.Patient(legacy_id=52, ramq='TEST01161973')
    bart_patient = patient_factories.Patient(legacy_id=53, ramq='TEST01161974')
    lisa_patient = patient_factories.Patient(legacy_id=54, ramq='TEST01161975')
    # marge
    marge_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        caregiver=marge_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    # homer
    marge_homer_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.guardian_caregiver(),
        patient=homer_patient,
        caregiver=marge_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    homer_first_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=homer_patient,
        caregiver=homer_caregiver,
        status=patient_models.RelationshipStatus.PENDING,
    )
    homer_second_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=homer_patient,
        caregiver=homer_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    # bart
    marge_bart_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.guardian_caregiver(),
        patient=bart_patient,
        caregiver=marge_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    bart_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=bart_patient,
        caregiver=bart_caregiver,
        status=patient_models.RelationshipStatus.EXPIRED,
    )
    # lisa
    homer_lisa_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.guardian_caregiver(),
        patient=lisa_patient,
        caregiver=homer_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    lisa_first_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=lisa_patient,
        caregiver=lisa_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    lisa_second_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=lisa_patient,
        caregiver=lisa_caregiver,
        status=patient_models.RelationshipStatus.PENDING,
    )

    caregiver_models.RegistrationCode.objects.bulk_create([
        caregiver_models.RegistrationCode(
            code='marge_code',
            relationship=marge_self_relationship,
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='marge_homer',
            relationship=marge_homer_relationship,
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='homer_self1',
            relationship=homer_first_self_relationship,
            status=caregiver_models.RegistrationCodeStatus.BLOCKED,
        ),
        caregiver_models.RegistrationCode(
            code='homer_self2',
            relationship=homer_second_self_relationship,
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='marge_bart',
            relationship=marge_bart_relationship,
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='bart_self',
            relationship=bart_self_relationship,
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='homer_lisa',
            relationship=homer_lisa_relationship,
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='lisa_self2',
            relationship=lisa_second_self_relationship,
            status=caregiver_models.RegistrationCodeStatus.NEW,
        ),
    ])
    # Lisa's registration code created on previous day
    today = timezone.now().date()
    previous_day = timezone.now() - dt.timedelta(days=1)
    mock_timezone = mocker.patch('django.utils.timezone.now')
    mock_timezone.return_value = previous_day
    caregiver_factories.RegistrationCode(
        code='lisa_self1',
        relationship=lisa_first_self_relationship,
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )

    population_summary = stats_queries.fetch_registration_summary(
        start_date=today,
        end_date=today,
    )
    assert population_summary == {
        'uncompleted_registration': 2,
        'completed_registration': 6,
    }


def test_empty_fetch_caregivers_summary() -> None:
    """Ensure fetch_caregivers_summary() query can return an empty result without errors."""
    caregivers_summary = stats_queries.fetch_caregivers_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert caregivers_summary == {
        'total': 0,
        'en': 0,
        'fr': 0,
    }


def test_fetch_caregivers_summary() -> None:
    """Ensure fetch_caregivers_summary() query successfully returns caregivers statistics."""
    caregiver_factories.Caregiver(username='marge', language='fr')
    caregiver_factories.Caregiver(username='homer', language='fr')
    caregiver_factories.Caregiver(username='bart')
    caregiver_factories.Caregiver(username='lisa')
    caregiver_factories.Caregiver(username='mona', language='fr')
    caregiver_factories.Caregiver(username='fred')
    caregiver_factories.Caregiver(
        username='pebbles', language='fr', date_joined=timezone.now() - dt.timedelta(days=1),
    )
    caregiver_factories.Caregiver(
        username='flinstone', language='fr', date_joined=timezone.now() - dt.timedelta(days=1),
    )
    caregivers_summary = stats_queries.fetch_caregivers_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert caregivers_summary == {
        'total': 6,
        'en': 3,
        'fr': 3,
    }


def test_empty_fetch_patients_summary() -> None:
    """Ensure fetch_patients_summary() query can return an empty result without errors."""
    caregivers_summary = stats_queries.fetch_patients_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert caregivers_summary == {
        'total': 0,
        'deceased': 0,
        'male': 0,
        'female': 0,
        'sex_other': 0,
        'sex_unknown': 0,
        'access_all': 0,
        'access_ntk': 0,
    }


def test_fetch_patients_summary() -> None:
    """Ensure fetch_patients_summary() query successfully returns patients statistics."""
    patient_factories.Patient(
        legacy_id=51, ramq='TEST01161974', sex=patient_models.Patient.SexType.FEMALE,
    )
    patient_factories.Patient(
        legacy_id=52, ramq='TEST01161975', sex=patient_models.Patient.SexType.OTHER,
    )
    patient_factories.Patient(
        legacy_id=53, ramq='TEST01161976', sex=patient_models.Patient.SexType.UNKNOWN,
    )
    patient_factories.Patient(
        legacy_id=54, ramq='TEST01161977', data_access=patient_models.Patient.DataAccessType.NEED_TO_KNOW,
    )
    patient_factories.Patient(
        legacy_id=55, ramq='TEST01161978', data_access=patient_models.Patient.DataAccessType.NEED_TO_KNOW,
    )
    patient_factories.Patient(
        legacy_id=56, ramq='TEST01161979', sex=patient_models.Patient.SexType.FEMALE, date_of_death=timezone.now(),
    )
    patient_factories.Patient(
        legacy_id=57, ramq='TEST01161980', date_of_death=timezone.now(),
    )
    patient_factories.Patient(
        legacy_id=58,
        ramq='TEST01161981',
        sex=patient_models.Patient.SexType.FEMALE,
        created_at=timezone.now() - dt.timedelta(days=3),
    )
    caregivers_summary = stats_queries.fetch_patients_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert caregivers_summary == {
        'total': 7,
        'deceased': 2,
        'male': 3,
        'female': 2,
        'sex_other': 1,
        'sex_unknown': 1,
        'access_all': 5,
        'access_ntk': 2,
    }


@pytest.mark.django_db(databases=['legacy'])
def test_empty_fetch_devices_summary() -> None:
    """Ensure fetch_devices_summary() query can return an empty result without errors."""
    devices_summary = stats_queries.fetch_devices_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert devices_summary == {
        'device_total': 0,
        'device_ios': 0,
        'device_android': 0,
        'device_browser': 0,
    }


@pytest.mark.django_db(databases=['legacy'])
def test_fetch_devices_summary(mocker: MockerFixture) -> None:
    """Ensure fetch_devices_summary() query successfully returns device statistics."""
    legacy_factories.LegacyPatientDeviceIdentifierFactory()
    legacy_factories.LegacyPatientDeviceIdentifierFactory()
    legacy_factories.LegacyPatientDeviceIdentifierFactory(device_type=1)
    legacy_factories.LegacyPatientDeviceIdentifierFactory(device_type=1)
    legacy_factories.LegacyPatientDeviceIdentifierFactory(device_type=3)
    legacy_factories.LegacyPatientDeviceIdentifierFactory(device_type=3)

    # Previous day records
    previous_day = timezone.now() - dt.timedelta(days=1)
    mock_timezone = mocker.patch('django.utils.timezone.now')
    mock_timezone.return_value = previous_day
    legacy_factories.LegacyPatientDeviceIdentifierFactory(last_updated=previous_day)
    legacy_factories.LegacyPatientDeviceIdentifierFactory(device_type=1, last_updated=previous_day)
    devices_summary = stats_queries.fetch_devices_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert devices_summary == {
        'device_total': 6,
        'device_ios': 2,
        'device_android': 2,
        'device_browser': 2,
    }


def test_empty_fetch_patients_received_data_summary() -> None:
    """Ensure fetch_patients_received_data_summary() query can return an empty result without errors."""
    patients_received_data_summary = stats_queries.fetch_patients_received_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert patients_received_data_summary == {
        'no_appointment_labs_notes': 0,
        'has_appointment_only': 0,
        'has_labs_only': 0,
        'has_clinical_notes_only': 0,
        'using_app_after_receiving_new_data': 0,
        'not_using_app_after_receiving_new_data': 0,
        'not_using_app_and_no_data': 0,
    }


def test_patients_received_data_no_appointment_labs_note() -> None:
    """Ensure fetch_patients_received_data_summary() query successfully returns patients received data statistics."""
    relationships = _create_registration_and_relationship_records()

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['bart_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )
    # Lisa's received records should not be included to the no_appointment_labs_notes count
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )

    # previous day received records should not be included to the no_appointment_labs_notes count

    stats_factories.DailyPatientDataReceived(patient=relationships['marge_relationship'].patient)
    stats_factories.DailyPatientDataReceived(patient=relationships['homer_relationship'].patient)
    stats_factories.DailyPatientDataReceived(patient=relationships['bart_relationship'].patient)
    stats_factories.DailyPatientDataReceived(patient=relationships['lisa_relationship'].patient)

    patients_received_data_summary = stats_queries.fetch_patients_received_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )

    assert stats_models.DailyPatientDataReceived.objects.count() == 8
    assert patients_received_data_summary == {
        'no_appointment_labs_notes': 3,
        'has_appointment_only': 0,
        'has_labs_only': 0,
        'has_clinical_notes_only': 0,
        'using_app_after_receiving_new_data': 0,
        'not_using_app_after_receiving_new_data': 0,
        'not_using_app_and_no_data': 0,
    }


def _create_registration_and_relationship_records() -> dict[str, Any]:
    """Create registration codes and relationships for 4 patients.

    The records are created for Marge, Homer, Bart, and Lisa.

    Returns:
        dictionary with self relationships
    """
    marge_self_relationship = patient_factories.Relationship(
        type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        caregiver=caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(username='marge', last_login=timezone.now()),
            legacy_id=1,
        ),
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    homer_self_relationship = patient_factories.Relationship(
        type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        caregiver=caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(
                username='homer',
                last_login=timezone.now() - dt.timedelta(days=1),
            ),
            legacy_id=2,
        ),
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    bart_self_relationship = patient_factories.Relationship(
        type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        caregiver=caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(
                username='bart',
                last_login=timezone.now() - dt.timedelta(days=2),
            ),
            legacy_id=3,
        ),
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    lisa_self_relationship = patient_factories.Relationship(
        type=patient_factories.RelationshipType(role_type=patient_models.RoleType.SELF),
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        caregiver=caregiver_factories.CaregiverProfile(
            user=caregiver_factories.Caregiver(
                username='lisa',
                last_login=None,
            ),
            legacy_id=4,
        ),
        status=patient_models.RelationshipStatus.CONFIRMED,
    )

    caregiver_factories.RegistrationCode(
        relationship=marge_self_relationship,
        code='marge1234567',
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        relationship=homer_self_relationship,
        code='homer1234567',
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        relationship=bart_self_relationship,
        code='bart12345678',
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        relationship=lisa_self_relationship,
        code='lisa12345678',
        status=caregiver_models.RegistrationCodeStatus.NEW,
    )

    return {
        'marge_relationship': marge_self_relationship,
        'homer_relationship': homer_self_relationship,
        'bart_relationship': bart_self_relationship,
        'lisa_relationship': lisa_self_relationship,
    }
