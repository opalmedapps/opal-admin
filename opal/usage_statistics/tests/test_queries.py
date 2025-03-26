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
        'total_registration_codes': 0,
    }


def test_fetch_registration_summary(mocker: MockerFixture) -> None:
    """Ensure fetch_registration_summary() query successfully returns registration statistics."""
    relationships = _create_relationship_records()

    caregiver_models.RegistrationCode.objects.bulk_create([
        caregiver_models.RegistrationCode(
            code='marge_code',
            relationship=relationships['marge_relationship'],
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='marge_homer',
            relationship=relationships['marge_homer_relationship'],
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='homer_self1',
            relationship=relationships['homer_relationship'],
            status=caregiver_models.RegistrationCodeStatus.BLOCKED,
        ),
        caregiver_models.RegistrationCode(
            code='homer_self2',
            relationship=relationships['homer_pending_relationship'],
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='marge_bart',
            relationship=relationships['marge_bart_relationship'],
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='bart_self',
            relationship=relationships['bart_relationship'],
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='homer_lisa',
            relationship=relationships['homer_lisa_relationship'],
            status=caregiver_models.RegistrationCodeStatus.REGISTERED,
        ),
        caregiver_models.RegistrationCode(
            code='lisa_self2',
            relationship=relationships['lisa_pending_relationship'],
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
        relationship=relationships['lisa_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )

    population_summary = stats_queries.fetch_registration_summary(
        start_date=today,
        end_date=today,
    )
    assert population_summary == {
        'uncompleted_registration': 2,
        'completed_registration': 6,
        'total_registration_codes': 8,
    }


def test_empty_fetch_grouped_registration_summary() -> None:
    """Ensure fetch_grouped_registration_summary() query can return an empty result without errors."""
    registration_summary = stats_queries.fetch_grouped_registration_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not registration_summary


def test_fetch_grouped_registration_summary_by_day(mocker: MockerFixture) -> None:
    """Ensure fetch_grouped_registration_summary query successfully returns registration statistics grouped by day."""
    relationships = _create_relationship_records()
    current_datetime = timezone.localtime()
    mock_timezone = mocker.patch('django.utils.timezone.now')
    mock_timezone.return_value = current_datetime
    caregiver_factories.RegistrationCode(
        code='marge_code',
        relationship=relationships['marge_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = current_datetime - dt.timedelta(days=1)
    caregiver_factories.RegistrationCode(
        code='marge_homer',
        relationship=relationships['marge_homer_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='homer_self',
        relationship=relationships['homer_relationship'],
        status=caregiver_models.RegistrationCodeStatus.BLOCKED,
    )
    mock_timezone.return_value = current_datetime - dt.timedelta(days=4)
    caregiver_factories.RegistrationCode(
        code='marge_bart',
        relationship=relationships['marge_bart_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='bart_self',
        relationship=relationships['bart_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = current_datetime - dt.timedelta(days=6)
    caregiver_factories.RegistrationCode(
        code='homer_lisa',
        relationship=relationships['homer_lisa_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='lisa_self',
        relationship=relationships['lisa_pending_relationship'],
        status=caregiver_models.RegistrationCodeStatus.NEW,
    )

    population_summary = stats_queries.fetch_grouped_registration_summary(
        start_date=current_datetime.today() - dt.timedelta(days=7),
        end_date=current_datetime.today(),
    )

    current_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    assert population_summary == [
        {
            'uncompleted_registration': 0,
            'completed_registration': 1,
            'total_registration_codes': 1,
            'date': current_datetime,
        },
        {
            'uncompleted_registration': 1,
            'completed_registration': 1,
            'total_registration_codes': 2,
            'date': current_datetime - dt.timedelta(days=1),
        },
        {
            'uncompleted_registration': 0,
            'completed_registration': 2,
            'total_registration_codes': 2,
            'date': current_datetime - dt.timedelta(days=4),
        },
        {
            'uncompleted_registration': 1,
            'completed_registration': 1,
            'total_registration_codes': 2,
            'date': current_datetime - dt.timedelta(days=6),
        },
    ]


def test_fetch_grouped_registration_summary_by_month(mocker: MockerFixture) -> None:
    """Ensure fetch_grouped_registration_summary() successfully returns registration statistics grouped by month."""
    relationships = _create_relationship_records()

    mock_timezone = mocker.patch('django.utils.timezone.now')
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 6, 20))
    caregiver_factories.RegistrationCode(
        code='marge_code',
        relationship=relationships['marge_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 5, 15))
    caregiver_factories.RegistrationCode(
        code='marge_homer',
        relationship=relationships['marge_homer_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 5, 10))
    caregiver_factories.RegistrationCode(
        code='homer_self',
        relationship=relationships['homer_relationship'],
        status=caregiver_models.RegistrationCodeStatus.BLOCKED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 4, 10))
    caregiver_factories.RegistrationCode(
        code='marge_bart',
        relationship=relationships['marge_bart_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 4, 5))
    caregiver_factories.RegistrationCode(
        code='bart_self',
        relationship=relationships['bart_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 3, 4))
    caregiver_factories.RegistrationCode(
        code='homer_lisa',
        relationship=relationships['homer_lisa_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 3, 1))
    caregiver_factories.RegistrationCode(
        code='lisa_self',
        relationship=relationships['lisa_pending_relationship'],
        status=caregiver_models.RegistrationCodeStatus.NEW,
    )

    population_summary = stats_queries.fetch_grouped_registration_summary(
        start_date=dt.date(2024, 3, 1),
        end_date=dt.date(2024, 6, 20),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert population_summary == [
        {
            'uncompleted_registration': 0,
            'completed_registration': 1,
            'total_registration_codes': 1,
            'month': timezone.make_aware(dt.datetime(2024, 6, 1)),
        },
        {
            'uncompleted_registration': 1,
            'completed_registration': 1,
            'total_registration_codes': 2,
            'month': timezone.make_aware(dt.datetime(2024, 5, 1)),
        },
        {
            'uncompleted_registration': 0,
            'completed_registration': 2,
            'total_registration_codes': 2,
            'month': timezone.make_aware(dt.datetime(2024, 4, 1)),
        },
        {
            'uncompleted_registration': 1,
            'completed_registration': 1,
            'total_registration_codes': 2,
            'month': timezone.make_aware(dt.datetime(2024, 3, 1)),
        },
    ]


def test_fetch_grouped_registration_summary_by_year(mocker: MockerFixture) -> None:
    """Ensure fetch_grouped_registration_summary() successfully returns registration statistics grouped by year."""
    relationships = _create_relationship_records()

    mock_timezone = mocker.patch('django.utils.timezone.now')
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2024, 6, 20))
    caregiver_factories.RegistrationCode(
        code='marge_code',
        relationship=relationships['marge_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2023, 5, 15))
    caregiver_factories.RegistrationCode(
        code='marge_homer',
        relationship=relationships['marge_homer_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2023, 4, 10))
    caregiver_factories.RegistrationCode(
        code='homer_self',
        relationship=relationships['homer_relationship'],
        status=caregiver_models.RegistrationCodeStatus.BLOCKED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2022, 4, 10))
    caregiver_factories.RegistrationCode(
        code='marge_bart',
        relationship=relationships['marge_bart_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2022, 3, 5))
    caregiver_factories.RegistrationCode(
        code='bart_self',
        relationship=relationships['bart_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2021, 2, 4))
    caregiver_factories.RegistrationCode(
        code='homer_lisa',
        relationship=relationships['homer_lisa_relationship'],
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    mock_timezone.return_value = timezone.make_aware(dt.datetime(2021, 1, 1))
    caregiver_factories.RegistrationCode(
        code='lisa_self',
        relationship=relationships['lisa_pending_relationship'],
        status=caregiver_models.RegistrationCodeStatus.NEW,
    )

    population_summary = stats_queries.fetch_grouped_registration_summary(
        start_date=dt.date(2021, 1, 1),
        end_date=dt.date(2024, 6, 20),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert population_summary == [
        {
            'uncompleted_registration': 0,
            'completed_registration': 1,
            'total_registration_codes': 1,
            'year': timezone.make_aware(dt.datetime(2024, 1, 1)),
        },
        {
            'uncompleted_registration': 1,
            'completed_registration': 1,
            'total_registration_codes': 2,
            'year': timezone.make_aware(dt.datetime(2023, 1, 1)),
        },
        {
            'uncompleted_registration': 0,
            'completed_registration': 2,
            'total_registration_codes': 2,
            'year': timezone.make_aware(dt.datetime(2022, 1, 1)),
        },
        {
            'uncompleted_registration': 1,
            'completed_registration': 1,
            'total_registration_codes': 2,
            'year': timezone.make_aware(dt.datetime(2021, 1, 1)),
        },
    ]


def test_empty_fetch_caregivers_summary() -> None:
    """Ensure fetch_caregivers_summary() query can return an empty result without errors."""
    caregivers_summary = stats_queries.fetch_caregivers_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert caregivers_summary == {
        'caregivers_total': 0,
        'caregivers_registered': 0,
        'caregivers_unregistered': 0,
        'never_logged_in_after_registration': 0,
        'en': 0,
        'fr': 0,
    }


def test_fetch_caregivers_summary() -> None:
    """Ensure fetch_caregivers_summary() query successfully returns caregivers statistics."""
    caregiver_factories.Caregiver(username='marge', language='fr', last_login=timezone.now())
    caregiver_factories.Caregiver(username='homer', language='fr', last_login=timezone.now())
    caregiver_factories.Caregiver(username='bart')
    caregiver_factories.Caregiver(username='lisa', is_active=False)
    caregiver_factories.Caregiver(username='mona', language='fr', is_active=False)
    caregiver_factories.Caregiver(username='fred', is_active=False)
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
        'caregivers_total': 6,
        'caregivers_registered': 3,
        'caregivers_unregistered': 3,
        'never_logged_in_after_registration': 1,
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


def test_empty_fetch_patients_received_clinical_data_summary() -> None:
    """Ensure fetch_patients_received_clinical_data_summary() query can return an empty result without errors."""
    patients_received_data_summary = stats_queries.fetch_patients_received_clinical_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert patients_received_data_summary == {
        'no_appointments_labs_notes': 0,
        'has_appointments_only': 0,
        'has_labs_only': 0,
        'has_clinical_notes_only': 0,
        'receiving_new_data_total': 0,
    }


def test_patients_received_data_no_appointment_labs_note() -> None:
    """Ensure received_clinical_data_summary query successfully returns no_appointments_labs_notes statistic."""
    relationships = _create_relationship_records()

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
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )

    # previous day received records should not be included to the no_appointments_labs_notes count

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['bart_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
    )

    patients_received_data_summary = stats_queries.fetch_patients_received_clinical_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )

    assert stats_models.DailyPatientDataReceived.objects.count() == 8
    assert patients_received_data_summary == {
        'no_appointments_labs_notes': 4,
        'has_appointments_only': 0,
        'has_labs_only': 0,
        'has_clinical_notes_only': 0,
        'receiving_new_data_total': 0,
    }


def test_patients_received_data_has_appointments_only() -> None:
    """Ensure received_clinical_data_summary() query successfully returns has_appointments_only statistic."""
    relationships = _create_relationship_records()

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
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
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )

    # previous day received records should not be included to the has_appointments_only count

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['bart_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
    )

    patients_received_data_summary = stats_queries.fetch_patients_received_clinical_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )

    assert stats_models.DailyPatientDataReceived.objects.count() == 8
    assert patients_received_data_summary == {
        'no_appointments_labs_notes': 1,
        'has_appointments_only': 3,
        'has_labs_only': 0,
        'has_clinical_notes_only': 0,
        'receiving_new_data_total': 3,
    }


def test_patients_received_data_has_labs_only() -> None:
    """Ensure received_clinical_data_summary() query successfully returns has_labs_only statistic."""
    relationships = _create_relationship_records()

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
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
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        action_date=dt.date.today(),
    )

    # previous day received records should not be included to the has_labs_only count

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['bart_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
    )

    patients_received_data_summary = stats_queries.fetch_patients_received_clinical_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )

    assert stats_models.DailyPatientDataReceived.objects.count() == 8
    assert patients_received_data_summary == {
        'no_appointments_labs_notes': 1,
        'has_appointments_only': 0,
        'has_labs_only': 3,
        'has_clinical_notes_only': 0,
        'receiving_new_data_total': 3,
    }


def test_patients_received_data_has_clinical_notes_only() -> None:
    """Ensure received_clinical_data_summary() query successfully returns has_clinical_notes_only statistic."""
    relationships = _create_relationship_records()

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_appointment_received=None,
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
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )

    # previous day received records should not be included to the has_clinical_notes_only count

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['bart_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
    )

    patients_received_data_summary = stats_queries.fetch_patients_received_clinical_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )

    assert stats_models.DailyPatientDataReceived.objects.count() == 8
    assert patients_received_data_summary == {
        'no_appointments_labs_notes': 1,
        'has_appointments_only': 0,
        'has_labs_only': 0,
        'has_clinical_notes_only': 3,
        'receiving_new_data_total': 3,
    }


def test_patients_received_data_using_app_after_receiving_new_data() -> None:
    """Ensure received_clinical_data_summary() successfully returns using_app_after_receiving_new_data count."""
    relationships = _create_relationship_records()

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['bart_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
        action_date=dt.date.today(),
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
        action_date=dt.date.today(),
    )

    # previous day received records should not be included to the using_app_after_receiving_new_data count

    stats_factories.DailyPatientDataReceived(
        patient=relationships['marge_relationship'].patient,
        last_document_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['homer_relationship'].patient,
        last_appointment_received=None,
        last_lab_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['bart_relationship'].patient,
        last_appointment_received=None,
        last_document_received=None,
    )
    stats_factories.DailyPatientDataReceived(
        patient=relationships['lisa_relationship'].patient,
    )

    patients_received_data_summary = stats_queries.fetch_patients_received_clinical_data_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )

    assert stats_models.DailyPatientDataReceived.objects.count() == 8
    assert patients_received_data_summary == {
        'no_appointments_labs_notes': 0,
        'has_appointments_only': 1,
        'has_labs_only': 1,
        'has_clinical_notes_only': 1,
        'receiving_new_data_total': 4,
    }


def test_empty_logins_summary() -> None:
    """Ensure fetch_logins_summary() query can return an empty result without errors."""
    logins_summary = stats_queries.fetch_logins_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not logins_summary


def test_fetch_logins_summary_by_date() -> None:
    """Ensure fetch_logins_summary() query successfully aggregates login statistics grouped by date."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    current_date = dt.datetime.now().date()
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=3,
        action_date=current_date - dt.timedelta(days=2),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=5,
        action_date=current_date - dt.timedelta(days=2),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=10,
        action_date=current_date,
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=3,
        action_date=current_date,
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=5,
        action_date=current_date,
    )

    logins_summary = stats_queries.fetch_logins_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )
    assert logins_summary == [
        {
            'date': current_date,
            'total_logins': 18,
            'unique_user_logins': 3,
            'avg_logins_per_user': 6,
        },
        {
            'date': current_date - dt.timedelta(days=2),
            'total_logins': 8,
            'unique_user_logins': 2,
            'avg_logins_per_user': 4,
        },
    ]


def test_fetch_logins_summary_by_month() -> None:
    """Ensure fetch_logins_summary() query successfully aggregates login statistics grouped by month."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=3,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=5,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=5,
        action_date=dt.date(2024, 4, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=1,
        action_date=dt.date(2024, 4, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=10,
        action_date=dt.date(2024, 3, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=9,
        action_date=dt.date(2024, 3, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=9,
        action_date=dt.date(2024, 3, 2),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=5,
        action_date=dt.date(2024, 3, 1),
    )

    logins_summary = stats_queries.fetch_logins_summary(
        start_date=dt.date(2024, 3, 1),
        end_date=dt.date(2024, 5, 5),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert stats_models.DailyUserAppActivity.objects.count() == 8
    assert logins_summary == [
        {
            'month': dt.date(2024, 5, 1),
            'total_logins': 8,
            'unique_user_logins': 2,
            'avg_logins_per_user': 4.0,
        },
        {
            'month': dt.date(2024, 4, 1),
            'total_logins': 6,
            'unique_user_logins': 2,
            'avg_logins_per_user': 3.0,
        },
        {
            'month': dt.date(2024, 3, 1),
            'total_logins': 33,
            'unique_user_logins': 3,
            'avg_logins_per_user': 11.0,
        },
    ]


def test_fetch_logins_summary_by_year() -> None:
    """Ensure fetch_logins_summary() query successfully aggregates login statistics grouped by year."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=3,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=5,
        action_date=dt.date(2024, 4, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=5,
        action_date=dt.date(2023, 8, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=6,
        action_date=dt.date(2023, 7, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=1,
        action_date=dt.date(2023, 6, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=3,
        action_date=dt.date(2023, 5, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=10,
        action_date=dt.date(2022, 4, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=8,
        action_date=dt.date(2022, 3, 3),
    )

    logins_summary = stats_queries.fetch_logins_summary(
        start_date=dt.date(2022, 2, 1),
        end_date=dt.date(2024, 5, 5),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert stats_models.DailyUserAppActivity.objects.count() == 8
    assert logins_summary == [
        {
            'year': dt.date(2024, 1, 1),
            'total_logins': 8,
            'unique_user_logins': 2,
            'avg_logins_per_user': 4.0,
        },
        {
            'year': dt.date(2023, 1, 1),
            'total_logins': 15,
            'unique_user_logins': 3,
            'avg_logins_per_user': 5.0,
        },
        {
            'year': dt.date(2022, 1, 1),
            'total_logins': 18,
            'unique_user_logins': 2,
            'avg_logins_per_user': 9.0,
        },
    ]


def test_empty_users_clicks_summary() -> None:
    """Ensure fetch_users_clicks_summary() query can return an empty result without errors."""
    users_clicks_summary = stats_queries.fetch_users_clicks_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not users_clicks_summary


def test_users_clicks_summary_by_date() -> None:
    """Ensure fetch_users_clicks_summary() query successfully aggregates users' click statistics grouped by date."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    current_date = dt.datetime.now().date()
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=3,
        count_feedback=4,
        count_update_security_answers=5,
        count_update_passwords=6,
        action_date=current_date - dt.timedelta(days=2),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=current_date - dt.timedelta(days=2),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=10,
        count_feedback=11,
        count_update_security_answers=12,
        count_update_passwords=13,
        action_date=current_date,
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=3,
        count_feedback=4,
        count_update_security_answers=5,
        count_update_passwords=6,
        action_date=current_date,
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=current_date,
    )

    users_clicks_summary = stats_queries.fetch_users_clicks_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )
    assert users_clicks_summary == [
        {
            'date': current_date,
            'login_count': 18,
            'feedback_count': 21,
            'update_security_answers_count': 24,
            'update_passwords_count': 27,
        },
        {
            'date': current_date - dt.timedelta(days=2),
            'login_count': 8,
            'feedback_count': 10,
            'update_security_answers_count': 12,
            'update_passwords_count': 14,
        },
    ]


def test_users_clicks_summary_by_month() -> None:
    """Ensure fetch_users_clicks_summary() query successfully aggregates users' click statistics grouped by month."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=3,
        count_feedback=4,
        count_update_security_answers=5,
        count_update_passwords=6,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=dt.date(2024, 4, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=6,
        count_feedback=7,
        count_update_security_answers=8,
        count_update_passwords=9,
        action_date=dt.date(2024, 4, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=1,
        count_feedback=2,
        count_update_security_answers=3,
        count_update_passwords=4,
        action_date=dt.date(2024, 4, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=10,
        count_feedback=11,
        count_update_security_answers=12,
        count_update_passwords=13,
        action_date=dt.date(2024, 3, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=9,
        count_feedback=10,
        count_update_security_answers=11,
        count_update_passwords=12,
        action_date=dt.date(2024, 3, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=dt.date(2024, 3, 1),
    )

    users_clicks_summary = stats_queries.fetch_users_clicks_summary(
        start_date=dt.date(2024, 3, 1),
        end_date=dt.date(2024, 5, 5),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert stats_models.DailyUserAppActivity.objects.count() == 8
    assert users_clicks_summary == [
        {
            'month': dt.date(2024, 5, 1),
            'login_count': 8,
            'feedback_count': 10,
            'update_security_answers_count': 12,
            'update_passwords_count': 14,
        },
        {
            'month': dt.date(2024, 4, 1),
            'login_count': 12,
            'feedback_count': 15,
            'update_security_answers_count': 18,
            'update_passwords_count': 21,
        },
        {
            'month': dt.date(2024, 3, 1),
            'login_count': 24,
            'feedback_count': 27,
            'update_security_answers_count': 30,
            'update_passwords_count': 33,
        },
    ]


def test_users_clicks_summary_by_year() -> None:
    """Ensure fetch_users_clicks_summary() query successfully aggregates users' click statistics grouped by year."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=3,
        count_feedback=4,
        count_update_security_answers=5,
        count_update_passwords=6,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=dt.date(2024, 4, 5),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=dt.date(2023, 8, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=6,
        count_feedback=7,
        count_update_security_answers=8,
        count_update_passwords=9,
        action_date=dt.date(2023, 7, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=1,
        count_feedback=2,
        count_update_security_answers=3,
        count_update_passwords=4,
        action_date=dt.date(2023, 6, 4),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        count_logins=10,
        count_feedback=11,
        count_update_security_answers=12,
        count_update_passwords=13,
        action_date=dt.date(2022, 4, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=9,
        count_feedback=10,
        count_update_security_answers=11,
        count_update_passwords=12,
        action_date=dt.date(2022, 3, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=5,
        count_feedback=6,
        count_update_security_answers=7,
        count_update_passwords=8,
        action_date=dt.date(2022, 2, 1),
    )

    users_clicks_summary = stats_queries.fetch_users_clicks_summary(
        start_date=dt.date(2022, 2, 1),
        end_date=dt.date(2024, 5, 5),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert stats_models.DailyUserAppActivity.objects.count() == 8
    assert users_clicks_summary == [
        {
            'year': dt.date(2024, 1, 1),
            'login_count': 8,
            'feedback_count': 10,
            'update_security_answers_count': 12,
            'update_passwords_count': 14,
        },
        {
            'year': dt.date(2023, 1, 1),
            'login_count': 12,
            'feedback_count': 15,
            'update_security_answers_count': 18,
            'update_passwords_count': 21,
        },
        {
            'year': dt.date(2022, 1, 1),
            'login_count': 24,
            'feedback_count': 27,
            'update_security_answers_count': 30,
            'update_passwords_count': 33,
        },
    ]


def test_user_patient_clicks_summary_by_date() -> None:
    """Ensure fetch_user_patient_clicks_summary() successfully aggregates user/patient clicks grouped by date."""
    relationships = _create_relationship_records()
    current_date = dt.datetime.now().date()

    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=current_date - dt.timedelta(days=2),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=10,
        count_documents=11,
        count_educational_materials=12,
        count_questionnaires_complete=13,
        count_labs=14,
        action_date=current_date - dt.timedelta(days=2),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['bart_relationship'],
        action_by_user=relationships['bart_relationship'].caregiver.user,
        patient=relationships['bart_relationship'].patient,
        count_checkins=5,
        count_documents=6,
        count_educational_materials=7,
        count_questionnaires_complete=8,
        count_labs=9,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=7,
        count_documents=8,
        count_educational_materials=9,
        count_questionnaires_complete=10,
        count_labs=11,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=1,
        count_documents=2,
        count_educational_materials=3,
        count_questionnaires_complete=4,
        count_labs=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=1,
        count_documents=2,
        count_educational_materials=3,
        count_questionnaires_complete=4,
        count_labs=5,
        action_date=current_date,
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=current_date,
    )

    user_patient_clicks_summary = stats_queries.fetch_user_patient_clicks_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )
    assert stats_models.DailyUserPatientActivity.objects.count() == 8
    assert user_patient_clicks_summary == [
        {
            'date': current_date,
            'checkins_count': 4,
            'documents_count': 6,
            'educational_materials_count': 8,
            'completed_questionnaires_count': 10,
            'labs_count': 12,
        },
        {
            'date': current_date - dt.timedelta(days=1),
            'checkins_count': 16,
            'documents_count': 20,
            'educational_materials_count': 24,
            'completed_questionnaires_count': 28,
            'labs_count': 32,
        },
        {
            'date': current_date - dt.timedelta(days=2),
            'checkins_count': 13,
            'documents_count': 15,
            'educational_materials_count': 17,
            'completed_questionnaires_count': 19,
            'labs_count': 21,
        },
    ]


def test_user_patient_clicks_summary_by_month() -> None:
    """Ensure fetch_user_patient_clicks_summary() successfully aggregates user/patient clicks grouped by month."""
    relationships = _create_relationship_records()

    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=10,
        count_documents=11,
        count_educational_materials=12,
        count_questionnaires_complete=13,
        count_labs=14,
        action_date=dt.date(2024, 5, 4),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['bart_relationship'],
        action_by_user=relationships['bart_relationship'].caregiver.user,
        patient=relationships['bart_relationship'].patient,
        count_checkins=5,
        count_documents=6,
        count_educational_materials=7,
        count_questionnaires_complete=8,
        count_labs=9,
        action_date=dt.date(2024, 4, 4),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=7,
        count_documents=8,
        count_educational_materials=9,
        count_questionnaires_complete=10,
        count_labs=11,
        action_date=dt.date(2024, 4, 3),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=1,
        count_documents=2,
        count_educational_materials=3,
        count_questionnaires_complete=4,
        count_labs=5,
        action_date=dt.date(2024, 4, 2),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.date(2024, 4, 1),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=1,
        count_documents=2,
        count_educational_materials=3,
        count_questionnaires_complete=4,
        count_labs=5,
        action_date=dt.date(2024, 3, 3),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.date(2024, 3, 1),
    )

    user_patient_clicks_summary = stats_queries.fetch_user_patient_clicks_summary(
        start_date=dt.date(2024, 3, 1),
        end_date=dt.date(2024, 5, 5),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert stats_models.DailyUserPatientActivity.objects.count() == 8
    assert user_patient_clicks_summary == [
        {
            'month': dt.date(2024, 5, 1),
            'checkins_count': 13,
            'documents_count': 15,
            'educational_materials_count': 17,
            'completed_questionnaires_count': 19,
            'labs_count': 21,
        },
        {
            'month': dt.date(2024, 4, 1),
            'checkins_count': 16,
            'documents_count': 20,
            'educational_materials_count': 24,
            'completed_questionnaires_count': 28,
            'labs_count': 32,
        },
        {
            'month': dt.date(2024, 3, 1),
            'checkins_count': 4,
            'documents_count': 6,
            'educational_materials_count': 8,
            'completed_questionnaires_count': 10,
            'labs_count': 12,
        },
    ]


def test_user_patient_clicks_summary_by_year() -> None:
    """Ensure fetch_user_patient_clicks_summary() successfully aggregates user/patient clicks grouped by year."""
    relationships = _create_relationship_records()

    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=10,
        count_documents=11,
        count_educational_materials=12,
        count_questionnaires_complete=13,
        count_labs=14,
        action_date=dt.date(2024, 4, 5),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['bart_relationship'],
        action_by_user=relationships['bart_relationship'].caregiver.user,
        patient=relationships['bart_relationship'].patient,
        count_checkins=5,
        count_documents=6,
        count_educational_materials=7,
        count_questionnaires_complete=8,
        count_labs=9,
        action_date=dt.date(2023, 5, 5),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=7,
        count_documents=8,
        count_educational_materials=9,
        count_questionnaires_complete=10,
        count_labs=11,
        action_date=dt.date(2023, 4, 4),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=1,
        count_documents=2,
        count_educational_materials=3,
        count_questionnaires_complete=4,
        count_labs=5,
        action_date=dt.date(2023, 3, 3),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.date(2023, 2, 2),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=1,
        count_documents=2,
        count_educational_materials=3,
        count_questionnaires_complete=4,
        count_labs=5,
        action_date=dt.date(2022, 3, 3),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.date(2022, 2, 1),
    )

    user_patient_clicks_summary = stats_queries.fetch_user_patient_clicks_summary(
        start_date=dt.date(2022, 2, 1),
        end_date=dt.date(2024, 5, 5),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert stats_models.DailyUserPatientActivity.objects.count() == 8
    assert user_patient_clicks_summary == [
        {
            'year': dt.date(2024, 1, 1),
            'checkins_count': 13,
            'documents_count': 15,
            'educational_materials_count': 17,
            'completed_questionnaires_count': 19,
            'labs_count': 21,
        },
        {
            'year': dt.date(2023, 1, 1),
            'checkins_count': 16,
            'documents_count': 20,
            'educational_materials_count': 24,
            'completed_questionnaires_count': 28,
            'labs_count': 32,
        },
        {
            'year': dt.date(2022, 1, 1),
            'checkins_count': 4,
            'documents_count': 6,
            'educational_materials_count': 8,
            'completed_questionnaires_count': 10,
            'labs_count': 12,
        },
    ]


def test_empty_received_labs_summary() -> None:
    """Ensure fetch_received_labs_summary() query can return an empty result without errors."""
    received_labs_summary = stats_queries.fetch_received_labs_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not received_labs_summary


def test_received_labs_summary_by_day() -> None:
    """Ensure fetch_received_labs_summary() query successfully aggregates received labs summary grouped by day."""
    current_date = dt.datetime.now().date()

    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        labs_received=5,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        labs_received=10,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        labs_received=15,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        labs_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        labs_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        labs_received=15,
        action_date=current_date - dt.timedelta(days=2),
    )

    received_labs_summary = stats_queries.fetch_received_labs_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )

    assert received_labs_summary == [
        {
            'total_received_labs': 30,
            'total_unique_patients': 3,
            'avg_received_labs_per_patient': 10,
            'date': current_date,
        },
        {
            'total_received_labs': 10,
            'total_unique_patients': 2,
            'avg_received_labs_per_patient': 5,
            'date': current_date - dt.timedelta(days=1),
        },
        {
            'total_received_labs': 15,
            'total_unique_patients': 1,
            'avg_received_labs_per_patient': 15,
            'date': current_date - dt.timedelta(days=2),
        },
    ]


def test_received_labs_summary_by_month() -> None:
    """Ensure fetch_received_labs_summary() query successfully aggregates received labs summary grouped by month."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        labs_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        labs_received=10,
        action_date=dt.date(2024, 6, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        labs_received=15,
        action_date=dt.date(2024, 6, 1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        labs_received=5,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        labs_received=5,
        action_date=dt.date(2024, 5, 2),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        labs_received=15,
        action_date=dt.date(2024, 4, 10),
    )

    received_labs_summary = stats_queries.fetch_received_labs_summary(
        start_date=dt.date(2024, 4, 10),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert received_labs_summary == [
        {
            'total_received_labs': 30,
            'total_unique_patients': 3,
            'avg_received_labs_per_patient': 10,
            'month': dt.date(2024, 6, 1),
        },
        {
            'total_received_labs': 10,
            'total_unique_patients': 2,
            'avg_received_labs_per_patient': 5,
            'month': dt.date(2024, 5, 1),
        },
        {
            'total_received_labs': 15,
            'total_unique_patients': 1,
            'avg_received_labs_per_patient': 15,
            'month': dt.date(2024, 4, 1),
        },
    ]


def test_received_labs_summary_by_year() -> None:
    """Ensure fetch_received_labs_summary() query successfully aggregates received labs summary grouped by year."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        labs_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        labs_received=10,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        labs_received=15,
        action_date=dt.date(2024, 4, 1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        labs_received=5,
        action_date=dt.date(2023, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        labs_received=5,
        action_date=dt.date(2023, 3, 2),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        labs_received=15,
        action_date=dt.date(2022, 2, 10),
    )

    received_labs_summary = stats_queries.fetch_received_labs_summary(
        start_date=dt.date(2022, 2, 10),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert received_labs_summary == [
        {
            'total_received_labs': 30,
            'total_unique_patients': 3,
            'avg_received_labs_per_patient': 10,
            'year': dt.date(2024, 1, 1),
        },
        {
            'total_received_labs': 10,
            'total_unique_patients': 2,
            'avg_received_labs_per_patient': 5,
            'year': dt.date(2023, 1, 1),
        },
        {
            'total_received_labs': 15,
            'total_unique_patients': 1,
            'avg_received_labs_per_patient': 15,
            'year': dt.date(2022, 1, 1),
        },
    ]


def test_empty_received_appointments_summary() -> None:
    """Ensure fetch_received_appointments_summary() query can return an empty result without errors."""
    received_appointments_summary = stats_queries.fetch_received_appointments_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not received_appointments_summary


def test_fetch_received_appointments_summary_by_day() -> None:
    """Ensure received_appointments_summary() successfully aggregates received appointments summary grouped by day."""
    current_date = dt.datetime.now().date()

    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        appointments_received=5,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        appointments_received=10,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        appointments_received=15,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        appointments_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        appointments_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        appointments_received=15,
        action_date=current_date - dt.timedelta(days=2),
    )

    received_appointments_summary = stats_queries.fetch_received_appointments_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )

    assert received_appointments_summary == [
        {
            'total_received_appointments': 30,
            'total_unique_patients': 3,
            'avg_received_appointments_per_patient': 10,
            'date': current_date,
        },
        {
            'total_received_appointments': 10,
            'total_unique_patients': 2,
            'avg_received_appointments_per_patient': 5,
            'date': current_date - dt.timedelta(days=1),
        },
        {
            'total_received_appointments': 15,
            'total_unique_patients': 1,
            'avg_received_appointments_per_patient': 15,
            'date': current_date - dt.timedelta(days=2),
        },
    ]


def test_fetch_received_appointments_summary_by_month() -> None:
    """Ensure received_appointments_summary() successfully aggregates received appointments summary grouped by month."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        appointments_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        appointments_received=10,
        action_date=dt.date(2024, 6, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        appointments_received=15,
        action_date=dt.date(2024, 6, 1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        appointments_received=5,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        appointments_received=5,
        action_date=dt.date(2024, 5, 2),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        appointments_received=15,
        action_date=dt.date(2024, 4, 1),
    )

    received_appointments_summary = stats_queries.fetch_received_appointments_summary(
        start_date=dt.date(2024, 4, 1),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert received_appointments_summary == [
        {
            'total_received_appointments': 30,
            'total_unique_patients': 3,
            'avg_received_appointments_per_patient': 10,
            'month': dt.date(2024, 6, 1),
        },
        {
            'total_received_appointments': 10,
            'total_unique_patients': 2,
            'avg_received_appointments_per_patient': 5,
            'month': dt.date(2024, 5, 1),
        },
        {
            'total_received_appointments': 15,
            'total_unique_patients': 1,
            'avg_received_appointments_per_patient': 15,
            'month': dt.date(2024, 4, 1),
        },
    ]


def test_fetch_received_appointments_summary_by_year() -> None:
    """Ensure received_appointments_summary() successfully aggregates received appointments summary grouped by year."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        appointments_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        appointments_received=10,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        appointments_received=15,
        action_date=dt.date(2024, 4, 1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        appointments_received=5,
        action_date=dt.date(2023, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        appointments_received=5,
        action_date=dt.date(2023, 4, 2),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        appointments_received=15,
        action_date=dt.date(2022, 3, 1),
    )

    received_appointments_summary = stats_queries.fetch_received_appointments_summary(
        start_date=dt.date(2022, 3, 1),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert received_appointments_summary == [
        {
            'total_received_appointments': 30,
            'total_unique_patients': 3,
            'avg_received_appointments_per_patient': 10,
            'year': dt.date(2024, 1, 1),
        },
        {
            'total_received_appointments': 10,
            'total_unique_patients': 2,
            'avg_received_appointments_per_patient': 5,
            'year': dt.date(2023, 1, 1),
        },
        {
            'total_received_appointments': 15,
            'total_unique_patients': 1,
            'avg_received_appointments_per_patient': 15,
            'year': dt.date(2022, 1, 1),
        },
    ]


def test_empty_received_educational_materials_summary() -> None:
    """Ensure fetch_received_educational_materials_summary() query can return an empty result without errors."""
    received_educational_materials_summary = stats_queries.fetch_received_educational_materials_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not received_educational_materials_summary


def test_fetch_received_educational_materials_summary_by_day() -> None:
    """Ensure received_edu_materials_summary() successfully aggregates received edu materials summary grouped by day."""
    current_date = dt.datetime.now().date()

    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        educational_materials_received=5,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        educational_materials_received=10,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        educational_materials_received=15,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        educational_materials_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        educational_materials_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        educational_materials_received=15,
        action_date=current_date - dt.timedelta(days=2),
    )

    received_educational_materials_summary = stats_queries.fetch_received_educational_materials_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )

    assert received_educational_materials_summary == [
        {
            'total_received_edu_materials': 30,
            'total_unique_patients': 3,
            'avg_received_edu_materials_per_patient': 10,
            'date': current_date,
        },
        {
            'total_received_edu_materials': 10,
            'total_unique_patients': 2,
            'avg_received_edu_materials_per_patient': 5,
            'date': current_date - dt.timedelta(days=1),
        },
        {
            'total_received_edu_materials': 15,
            'total_unique_patients': 1,
            'avg_received_edu_materials_per_patient': 15,
            'date': current_date - dt.timedelta(days=2),
        },
    ]


def test_fetch_received_educational_materials_summary_by_month() -> None:
    """Ensure received_edu_materials_summary successfully aggregates received edu materials summary grouped by month."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        educational_materials_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        educational_materials_received=10,
        action_date=dt.date(2024, 6, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        educational_materials_received=15,
        action_date=dt.date(2024, 6, 5),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        educational_materials_received=5,
        action_date=dt.date(2024, 5, 15),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        educational_materials_received=5,
        action_date=dt.date(2024, 5, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        educational_materials_received=15,
        action_date=dt.date(2024, 4, 3),
    )

    received_educational_materials_summary = stats_queries.fetch_received_educational_materials_summary(
        start_date=dt.date(2024, 4, 3),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert received_educational_materials_summary == [
        {
            'total_received_edu_materials': 30,
            'total_unique_patients': 3,
            'avg_received_edu_materials_per_patient': 10,
            'month': dt.date(2024, 6, 1),
        },
        {
            'total_received_edu_materials': 10,
            'total_unique_patients': 2,
            'avg_received_edu_materials_per_patient': 5,
            'month': dt.date(2024, 5, 1),
        },
        {
            'total_received_edu_materials': 15,
            'total_unique_patients': 1,
            'avg_received_edu_materials_per_patient': 15,
            'month': dt.date(2024, 4, 1),
        },
    ]


def test_fetch_received_educational_materials_summary_by_year() -> None:
    """Ensure received_edu_materials_summary successfully aggregates received edu materials summary grouped by year."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        educational_materials_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        educational_materials_received=10,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        educational_materials_received=15,
        action_date=dt.date(2024, 4, 5),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        educational_materials_received=5,
        action_date=dt.date(2023, 4, 15),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        educational_materials_received=5,
        action_date=dt.date(2023, 3, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        educational_materials_received=15,
        action_date=dt.date(2022, 2, 3),
    )

    received_educational_materials_summary = stats_queries.fetch_received_educational_materials_summary(
        start_date=dt.date(2022, 2, 3),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert received_educational_materials_summary == [
        {
            'total_received_edu_materials': 30,
            'total_unique_patients': 3,
            'avg_received_edu_materials_per_patient': 10,
            'year': dt.date(2024, 1, 1),
        },
        {
            'total_received_edu_materials': 10,
            'total_unique_patients': 2,
            'avg_received_edu_materials_per_patient': 5,
            'year': dt.date(2023, 1, 1),
        },
        {
            'total_received_edu_materials': 15,
            'total_unique_patients': 1,
            'avg_received_edu_materials_per_patient': 15,
            'year': dt.date(2022, 1, 1),
        },
    ]


def test_empty_received_documents_summary() -> None:
    """Ensure fetch_received_documents_summary() query can return an empty result without errors."""
    received_documents_summary = stats_queries.fetch_received_documents_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not received_documents_summary


def test_fetch_received_documents_summary_by_day() -> None:
    """Ensure fetch_received_documents_summary() successfully aggregates received documents summary grouped by day."""
    current_date = dt.datetime.now().date()

    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        documents_received=5,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        documents_received=10,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        documents_received=15,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        documents_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        documents_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        documents_received=15,
        action_date=current_date - dt.timedelta(days=2),
    )

    received_documents_summary = stats_queries.fetch_received_documents_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )

    assert received_documents_summary == [
        {
            'total_received_documents': 30,
            'total_unique_patients': 3,
            'avg_received_documents_per_patient': 10,
            'date': current_date,
        },
        {
            'total_received_documents': 10,
            'total_unique_patients': 2,
            'avg_received_documents_per_patient': 5,
            'date': current_date - dt.timedelta(days=1),
        },
        {
            'total_received_documents': 15,
            'total_unique_patients': 1,
            'avg_received_documents_per_patient': 15,
            'date': current_date - dt.timedelta(days=2),
        },
    ]


def test_fetch_received_documents_summary_by_month() -> None:
    """Ensure fetch_received_documents_summary() successfully aggregates received documents summary grouped by month."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        documents_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        documents_received=10,
        action_date=dt.date(2024, 6, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        documents_received=15,
        action_date=dt.date(2024, 6, 2),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        documents_received=5,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        documents_received=5,
        action_date=dt.date(2024, 5, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        documents_received=15,
        action_date=dt.date(2024, 4, 5),
    )

    received_documents_summary = stats_queries.fetch_received_documents_summary(
        start_date=dt.date(2024, 4, 5),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert received_documents_summary == [
        {
            'total_received_documents': 30,
            'total_unique_patients': 3,
            'avg_received_documents_per_patient': 10,
            'month': dt.date(2024, 6, 1),
        },
        {
            'total_received_documents': 10,
            'total_unique_patients': 2,
            'avg_received_documents_per_patient': 5,
            'month': dt.date(2024, 5, 1),
        },
        {
            'total_received_documents': 15,
            'total_unique_patients': 1,
            'avg_received_documents_per_patient': 15,
            'month': dt.date(2024, 4, 1),
        },
    ]


def test_fetch_received_documents_summary_by_year() -> None:
    """Ensure fetch_received_documents_summary() successfully aggregates received documents summary grouped by year."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        documents_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        documents_received=10,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        documents_received=15,
        action_date=dt.date(2024, 4, 2),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        documents_received=5,
        action_date=dt.date(2023, 4, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        documents_received=5,
        action_date=dt.date(2023, 3, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        documents_received=15,
        action_date=dt.date(2022, 2, 5),
    )

    received_documents_summary = stats_queries.fetch_received_documents_summary(
        start_date=dt.date(2022, 2, 5),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert received_documents_summary == [
        {
            'total_received_documents': 30,
            'total_unique_patients': 3,
            'avg_received_documents_per_patient': 10,
            'year': dt.date(2024, 1, 1),
        },
        {
            'total_received_documents': 10,
            'total_unique_patients': 2,
            'avg_received_documents_per_patient': 5,
            'year': dt.date(2023, 1, 1),
        },
        {
            'total_received_documents': 15,
            'total_unique_patients': 1,
            'avg_received_documents_per_patient': 15,
            'year': dt.date(2022, 1, 1),
        },
    ]


def test_empty_received_questionnaires_summary() -> None:
    """Ensure fetch_received_questionnaires_summary() query can return an empty result without errors."""
    received_questionnaires_summary = stats_queries.fetch_received_questionnaires_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not received_questionnaires_summary


def test_fetch_received_questionnaires_summary_by_day() -> None:
    """Ensure received_questionnaires_summary successfully aggregates received questionnaires summary grouped by day."""
    current_date = dt.datetime.now().date()

    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        questionnaires_received=5,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        questionnaires_received=10,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        questionnaires_received=15,
        action_date=current_date,
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        questionnaires_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        questionnaires_received=5,
        action_date=current_date - dt.timedelta(days=1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        questionnaires_received=15,
        action_date=current_date - dt.timedelta(days=2),
    )

    received_questionnaires_summary = stats_queries.fetch_received_questionnaires_summary(
        start_date=current_date - dt.timedelta(days=2),
        end_date=current_date,
    )

    assert received_questionnaires_summary == [
        {
            'total_received_questionnaires': 30,
            'total_unique_patients': 3,
            'avg_received_questionnaires_per_patient': 10,
            'date': current_date,
        },
        {
            'total_received_questionnaires': 10,
            'total_unique_patients': 2,
            'avg_received_questionnaires_per_patient': 5,
            'date': current_date - dt.timedelta(days=1),
        },
        {
            'total_received_questionnaires': 15,
            'total_unique_patients': 1,
            'avg_received_questionnaires_per_patient': 15,
            'date': current_date - dt.timedelta(days=2),
        },
    ]


def test_fetch_received_questionnaires_summary_by_month() -> None:
    """Ensure fetch_received_questionnaires_summary successfully aggregates questionnaires summary grouped by month."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        questionnaires_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        questionnaires_received=10,
        action_date=dt.date(2024, 6, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        questionnaires_received=15,
        action_date=dt.date(2024, 6, 15),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        questionnaires_received=5,
        action_date=dt.date(2024, 5, 15),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        questionnaires_received=5,
        action_date=dt.date(2024, 5, 5),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        questionnaires_received=15,
        action_date=dt.date(2024, 4, 3),
    )

    received_questionnaires_summary = stats_queries.fetch_received_questionnaires_summary(
        start_date=dt.date(2024, 4, 3),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.MONTH,
    )

    assert received_questionnaires_summary == [
        {
            'total_received_questionnaires': 30,
            'total_unique_patients': 3,
            'avg_received_questionnaires_per_patient': 10,
            'month': dt.date(2024, 6, 1),
        },
        {
            'total_received_questionnaires': 10,
            'total_unique_patients': 2,
            'avg_received_questionnaires_per_patient': 5,
            'month': dt.date(2024, 5, 1),
        },
        {
            'total_received_questionnaires': 15,
            'total_unique_patients': 1,
            'avg_received_questionnaires_per_patient': 15,
            'month': dt.date(2024, 4, 1),
        },
    ]


def test_fetch_received_questionnaires_summary_by_year() -> None:
    """Ensure fetch_received_questionnaires_summary successfully aggregates questionnaires summary grouped by year."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        questionnaires_received=5,
        action_date=dt.date(2024, 6, 25),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        questionnaires_received=10,
        action_date=dt.date(2024, 5, 20),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        questionnaires_received=15,
        action_date=dt.date(2024, 4, 15),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        questionnaires_received=5,
        action_date=dt.date(2023, 4, 15),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        questionnaires_received=5,
        action_date=dt.date(2023, 3, 5),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        questionnaires_received=15,
        action_date=dt.date(2022, 2, 3),
    )

    received_questionnaires_summary = stats_queries.fetch_received_questionnaires_summary(
        start_date=dt.date(2022, 2, 3),
        end_date=dt.date(2024, 6, 25),
        group_by=stats_queries.GroupByComponent.YEAR,
    )

    assert received_questionnaires_summary == [
        {
            'total_received_questionnaires': 30,
            'total_unique_patients': 3,
            'avg_received_questionnaires_per_patient': 10,
            'year': dt.date(2024, 1, 1),
        },
        {
            'total_received_questionnaires': 10,
            'total_unique_patients': 2,
            'avg_received_questionnaires_per_patient': 5,
            'year': dt.date(2023, 1, 1),
        },
        {
            'total_received_questionnaires': 15,
            'total_unique_patients': 1,
            'avg_received_questionnaires_per_patient': 15,
            'year': dt.date(2022, 1, 1),
        },
    ]


def test_fetch_user_last_login_year_report_empty() -> None:
    """Ensure fetch_daily_user_clicks_report successfully generated with empty data."""
    current_date = dt.datetime.now().date()
    user_last_login_year_report = stats_queries.fetch_user_last_login_year_report(current_date)
    assert not user_last_login_year_report['last_login_with_none_date']
    assert not user_last_login_year_report['last_login_with_the_year_2024']
    assert not user_last_login_year_report['last_login_with_the_year_2023']
    assert not user_last_login_year_report['last_login_with_the_year_2022']
    assert not user_last_login_year_report['last_login_with_the_year_2021']
    assert not user_last_login_year_report['last_login_with_the_year_2020']
    assert not user_last_login_year_report['last_login_with_the_year_2019']
    assert not user_last_login_year_report['last_login_with_the_year_2018']
    assert not user_last_login_year_report['last_login_with_the_year_2017']
    assert not user_last_login_year_report['last_login_with_the_year_2016']


def test_fetch_user_last_login_year_report_success() -> None:
    """Ensure fetch_daily_user_clicks_report successfully generated."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=None,
        count_logins=3,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        last_login=dt.datetime(2023, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2023, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    user_last_login_year_report = stats_queries.fetch_user_last_login_year_report(dt.datetime(2024, 8, 20))
    assert user_last_login_year_report['last_login_with_none_date'] == 1
    assert user_last_login_year_report['last_login_with_the_year_2024'] == 1
    assert user_last_login_year_report['last_login_with_the_year_2023'] == 1
    assert not user_last_login_year_report['last_login_with_the_year_2022']
    assert not user_last_login_year_report['last_login_with_the_year_2021']
    assert not user_last_login_year_report['last_login_with_the_year_2020']
    assert not user_last_login_year_report['last_login_with_the_year_2019']
    assert not user_last_login_year_report['last_login_with_the_year_2018']
    assert not user_last_login_year_report['last_login_with_the_year_2017']
    assert not user_last_login_year_report['last_login_with_the_year_2016']


def test_fetch_user_last_login_year_report_user_multiple_records() -> None:
    """Ensure fetch_daily_user_clicks_report successfully generated with same user in different years."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2022, 8, 20, 10, 10, 10).astimezone(),
        count_logins=3,
        action_date=dt.datetime(2022, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2023, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2023, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    user_last_login_year_report = stats_queries.fetch_user_last_login_year_report(dt.datetime(2024, 8, 20), 2019)
    assert not user_last_login_year_report['last_login_with_none_date']
    assert user_last_login_year_report['last_login_with_the_year_2024'] == 1
    assert not user_last_login_year_report['last_login_with_the_year_2023']
    assert not user_last_login_year_report['last_login_with_the_year_2022']
    assert not user_last_login_year_report['last_login_with_the_year_2021']
    assert not user_last_login_year_report['last_login_with_the_year_2020']
    assert not user_last_login_year_report['last_login_with_the_year_2019']


def test_fetch_user_last_login_year_report_daily_multiple_records() -> None:
    """Ensure fetch_daily_user_clicks_report successfully generated with different user in same years."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=3,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    user_last_login_year_report = stats_queries.fetch_user_last_login_year_report(dt.datetime(2024, 8, 20))
    assert not user_last_login_year_report['last_login_with_none_date']
    assert user_last_login_year_report['last_login_with_the_year_2024'] == 3
    assert not user_last_login_year_report['last_login_with_the_year_2023']
    assert not user_last_login_year_report['last_login_with_the_year_2022']
    assert not user_last_login_year_report['last_login_with_the_year_2021']
    assert not user_last_login_year_report['last_login_with_the_year_2020']
    assert not user_last_login_year_report['last_login_with_the_year_2019']
    assert not user_last_login_year_report['last_login_with_the_year_2018']
    assert not user_last_login_year_report['last_login_with_the_year_2017']
    assert not user_last_login_year_report['last_login_with_the_year_2016']


def test_fetch_basic_functionality_stats_report_empty() -> None:
    """Ensure fetch_basic_functionality_stats_report successfully generated with empty data."""
    patient_stats_report = stats_queries.fetch_basic_functionality_stats_report(dt.datetime.now().date())
    assert not patient_stats_report['received_nothing']
    assert not patient_stats_report['received_new_data']
    assert not patient_stats_report['received_only_appointment']
    assert not patient_stats_report['received_only_document']
    assert not patient_stats_report['received_only_lab']
    assert not patient_stats_report['received_only_educational_material']
    assert not patient_stats_report['received_only_questionnaire']


def test_fetch_basic_functionality_stats_report_success() -> None:
    """Ensure fetch_basic_functionality_stats_report successfully generated with success."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        last_educational_material_received=None,
        appointments_received=0,
        action_date=dt.date(2024, 8, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        last_document_received=None,
        last_lab_received=None,
        last_educational_material_received=None,
        last_questionnaire_received=None,
        appointments_received=10,
        action_date=dt.date(2024, 8, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        last_appointment_received=None,
        last_lab_received=None,
        last_educational_material_received=None,
        last_questionnaire_received=None,
        action_date=dt.date(2024, 8, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        last_appointment_received=None,
        last_document_received=None,
        last_educational_material_received=None,
        last_questionnaire_received=None,
        action_date=dt.date(2024, 8, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        last_questionnaire_received=None,
        action_date=dt.date(2024, 8, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=56, ramq='TEST01161977'),
        appointments_received=15,
        action_date=dt.date(2024, 8, 10),
    )
    patient_stats_report = stats_queries.fetch_basic_functionality_stats_report(dt.date(2024, 8, 10))
    assert not patient_stats_report['received_nothing']
    assert patient_stats_report['received_new_data'] == 6
    assert patient_stats_report['received_only_appointment'] == 1
    assert patient_stats_report['received_only_document'] == 1
    assert patient_stats_report['received_only_lab'] == 1
    assert patient_stats_report['received_only_educational_material'] == 1
    assert patient_stats_report['received_only_questionnaire'] == 1


def test_fetch_basic_functionality_stats_report_received_nothing() -> None:
    """Ensure fetch_basic_functionality_stats_report generated with patient who received no data."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=51, ramq='TEST01161972'),
        last_appointment_received=None,
        last_document_received=None,
        last_lab_received=None,
        last_educational_material_received=None,
        last_questionnaire_received=None,
        appointments_received=0,
        action_date=dt.date(2024, 8, 10),
    )
    patient_stats_report = stats_queries.fetch_basic_functionality_stats_report(dt.date(2024, 8, 10))
    assert patient_stats_report['received_nothing'] == 1
    assert not patient_stats_report['received_new_data']
    assert not patient_stats_report['received_only_appointment']
    assert not patient_stats_report['received_only_document']
    assert not patient_stats_report['received_only_lab']
    assert not patient_stats_report['received_only_educational_material']
    assert not patient_stats_report['received_only_questionnaire']


def test_fetch_patient_labs_statistics_report_empty() -> None:
    """Ensure fetch_patient_labs_statistics_report successfully generated with empty data."""
    patient_lab_report = stats_queries.fetch_patient_labs_statistics_report()
    assert not patient_lab_report


def test_fetch_patient_labs_statistics_report_success() -> None:
    """Ensure fetch_patient_labs_statistics_report successfully generated with success."""
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=55, ramq='TEST01161976'),
        last_lab_received=None,
        labs_received=0,
        action_date=dt.date(2024, 8, 10),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=56, ramq='TEST01161977'),
        last_lab_received=dt.datetime(2024, 8, 1, 10, 10, 10).astimezone(),
        labs_received=3,
        action_date=dt.date(2024, 8, 1),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=56, ramq='TEST01161977'),
        last_lab_received=dt.datetime(2024, 8, 2, 10, 10, 10).astimezone(),
        labs_received=5,
        action_date=dt.date(2024, 8, 2),
    )
    stats_factories.DailyPatientDataReceived(
        patient=patient_factories.Patient(legacy_id=56, ramq='TEST01161977'),
        last_lab_received=dt.datetime(2024, 8, 10, 10, 10, 10).astimezone(),
        labs_received=10,
        action_date=dt.date(2024, 8, 10),
    )
    patient_lab_report = stats_queries.fetch_patient_labs_statistics_report()
    assert patient_lab_report == [
        {
            'patient_sernum': 55,
            'first_received': None,
            'last_received': None,
            'number_test': 0,
            'number_lab_received': 0,
            'average_labs_per_test': None,
        },
        {
            'patient_sernum': 56,
            'first_received': dt.datetime(2024, 8, 1, 14, 10, 10, tzinfo=dt.timezone.utc),
            'last_received': dt.datetime(2024, 8, 10, 14, 10, 10, tzinfo=dt.timezone.utc),
            'number_test': 3,
            'number_lab_received': 18,
            'average_labs_per_test': 6,
        },
    ]


def test_fetch_individual_average_login_report_empty() -> None:
    """Ensure fetch_individual_average_login_report successfully generated with empty data."""
    average_login_report = stats_queries.fetch_individual_average_login_report()
    assert not average_login_report


def test_fetch_individual_average_login_report_success() -> None:
    """Ensure fetch_individual_average_login_report successfully generated."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    homer_caregiver = caregiver_factories.CaregiverProfile(user__username='homer', legacy_id=2)
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=3,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    average_login_report = stats_queries.fetch_individual_average_login_report()
    assert average_login_report == [
        {
            'user_id': marge_caregiver.user.id,
            'number_of_days': 1,
            'number_of_logins': 3,
            'average_login_per_day': 3,
        },
        {
            'user_id': homer_caregiver.user.id,
            'number_of_days': 1,
            'number_of_logins': 5,
            'average_login_per_day': 5,
        },
        {
            'user_id': bart_caregiver.user.id,
            'number_of_days': 1,
            'number_of_logins': 5,
            'average_login_per_day': 5,
        },
    ]


def test_fetch_individual_average_login_report_multiple_login() -> None:
    """Ensure fetch_individual_average_login_report successfully generated with user login multiple times."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=2,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    average_login_report = stats_queries.fetch_individual_average_login_report()
    assert average_login_report == [
        {
            'user_id': marge_caregiver.user.id,
            'number_of_days': 3,
            'number_of_logins': 12,
            'average_login_per_day': 4,
        },
    ]


def test_fetch_average_login_per_year_by_month_report_empty() -> None:
    """Ensure fetch_average_login_per_year_by_month_report successfully generated with empty data."""
    annual_login_report = stats_queries.fetch_average_login_per_year_by_month_report()
    assert not annual_login_report


def test_test_fetch_average_login_per_year_by_month_report_success() -> None:
    """Ensure fetch_average_login_per_year_by_month_report successfully generated with empty data."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 1, 20, 10, 10, 10).astimezone(),
        count_logins=2,
        action_date=dt.datetime(2024, 1, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 2, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 2, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2023, 4, 20, 10, 10, 10).astimezone(),
        count_logins=2,
        action_date=dt.datetime(2023, 4, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2023, 5, 20, 10, 10, 10).astimezone(),
        count_logins=3,
        action_date=dt.datetime(2023, 5, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2023, 10, 20, 10, 10, 10).astimezone(),
        count_logins=6,
        action_date=dt.datetime(2023, 10, 20),
    )
    annual_login_report = stats_queries.fetch_average_login_per_year_by_month_report()
    assert annual_login_report == [
        {
            'year': 2024,
            'january': 2,
            'february': 5,
            'march': None,
            'april': None,
            'may': None,
            'june': None,
            'july': None,
            'august': 5,
            'september': None,
            'october': None,
            'november': None,
            'december': None,
        },
        {
            'year': 2023,
            'january': None,
            'february': None,
            'march': None,
            'april': 2,
            'may': 3,
            'june': None,
            'july': None,
            'august': None,
            'september': None,
            'october': 6,
            'november': None,
            'december': None,
        },
    ]


def test_fetch_monthly_user_app_activity_log_report_empty() -> None:
    """Ensure fetch_monthly_user_app_activity_log_report successfully generated with empty data."""
    monthly_user_report = stats_queries.fetch_monthly_user_app_activity_log_report()
    assert not monthly_user_report


def test_fetch_monthly_user_app_activity_log_report_success() -> None:
    """Ensure fetch_monthly_user_app_activity_log_report successfully generated."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 1, 20, 10, 10, 10).astimezone(),
        count_logins=2,
        count_feedback=1,
        count_update_security_answers=3,
        count_update_passwords=7,
        action_date=dt.datetime(2024, 1, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 2, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        count_feedback=10,
        count_update_security_answers=8,
        count_update_passwords=4,
        action_date=dt.datetime(2024, 2, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        count_feedback=3,
        count_update_security_answers=1,
        count_update_passwords=4,
        action_date=dt.datetime(2024, 8, 20),
    )

    monthly_user_report = stats_queries.fetch_monthly_user_app_activity_log_report()
    assert monthly_user_report == [
        {
            'month': dt.date(2024, 8, 1),
            'login_count': 5,
            'feedback_count': 3,
            'update_security_answers_count': 1,
            'update_passwords_count': 4,
        },
        {
            'month': dt.date(2024, 2, 1),
            'login_count': 5,
            'feedback_count': 10,
            'update_security_answers_count': 8,
            'update_passwords_count': 4,
        },
        {
            'month': dt.date(2024, 1, 1),
            'login_count': 2,
            'feedback_count': 1,
            'update_security_answers_count': 3,
            'update_passwords_count': 7,
        },
    ]


def test_fetch_monthly_user_patient_activity_log_report_empty() -> None:
    """Ensure fetch_monthly_user_patient_activity_log_report successfully generated with empty data."""
    monthly_user_report = stats_queries.fetch_monthly_user_pat_activity_log_report()
    assert not monthly_user_report


def test_fetch_monthly_user_patient_activity_log_report_success() -> None:
    """Ensure fetch_monthly_user_patient_activity_log_report successfully generated."""
    relationships = _create_relationship_records()
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.datetime(2024, 2, 20),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=10,
        count_documents=11,
        count_educational_materials=12,
        count_questionnaires_complete=13,
        count_labs=14,
        action_date=dt.datetime(2024, 3, 20),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['bart_relationship'],
        action_by_user=relationships['bart_relationship'].caregiver.user,
        patient=relationships['bart_relationship'].patient,
        count_checkins=5,
        count_documents=6,
        count_educational_materials=7,
        count_questionnaires_complete=8,
        count_labs=9,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=7,
        count_documents=8,
        count_educational_materials=9,
        count_questionnaires_complete=10,
        count_labs=11,
        action_date=dt.datetime(2024, 8, 20),
    )

    monthly_user_report = stats_queries.fetch_monthly_user_pat_activity_log_report()
    assert monthly_user_report == [
        {
            'month': dt.date(2024, 8, 1),
            'checkins_count': 12,
            'documents_count': 14,
            'educational_materials_count': 16,
            'completed_questionnaires_count': 18,
            'labs_count': 20,
        },
        {
            'month': dt.date(2024, 3, 1),
            'checkins_count': 10,
            'documents_count': 11,
            'educational_materials_count': 12,
            'completed_questionnaires_count': 13,
            'labs_count': 14,
        },
        {
            'month': dt.date(2024, 2, 1),
            'checkins_count': 3,
            'documents_count': 4,
            'educational_materials_count': 5,
            'completed_questionnaires_count': 6,
            'labs_count': 7,
        },
    ]


def test_fetch_annually_user_app_activity_log_report_empty() -> None:
    """Ensure fetch_annually_user_app_activity_log_report successfully generated with empty data."""
    annually_user_report = stats_queries.fetch_annually_user_app_activity_log_report()
    assert not annually_user_report


def test_fetch_annually_user_app_activity_log_report_success() -> None:
    """Ensure fetch_annually_user_app_activity_log_report successfully generated."""
    marge_caregiver = caregiver_factories.CaregiverProfile(user__username='marge', legacy_id=1)
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 1, 20, 10, 10, 10).astimezone(),
        count_logins=2,
        count_feedback=3,
        count_update_security_answers=1,
        count_update_passwords=4,
        action_date=dt.datetime(2024, 1, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 2, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        count_feedback=10,
        count_update_security_answers=5,
        count_update_passwords=4,
        action_date=dt.datetime(2024, 2, 20),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=marge_caregiver.user,
        last_login=dt.datetime(2024, 8, 20, 10, 10, 10).astimezone(),
        count_logins=5,
        count_feedback=9,
        count_update_security_answers=0,
        count_update_passwords=3,
        action_date=dt.datetime(2024, 8, 20),
    )

    annually_user_report = stats_queries.fetch_annually_user_app_activity_log_report()
    assert annually_user_report == [
        {
            'year': dt.date(2024, 1, 1),
            'login_count': 12,
            'feedback_count': 22,
            'update_security_answers_count': 6,
            'update_passwords_count': 11,
        },
    ]


def test_fetch_annually_user_patient_activity_log_report_empty() -> None:
    """Ensure fetch_annually_user_patient_activity_log_report successfully generated with empty data."""
    annually_user_report = stats_queries.fetch_annually_user_pat_activity_log_report()
    assert not annually_user_report


def test_fetch_annually_user_patient_activity_log_report_success() -> None:
    """Ensure fetch_annually_user_patient_activity_log_report successfully generated."""
    relationships = _create_relationship_records()
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['homer_relationship'],
        action_by_user=relationships['homer_relationship'].caregiver.user,
        patient=relationships['homer_relationship'].patient,
        count_checkins=3,
        count_documents=4,
        count_educational_materials=5,
        count_questionnaires_complete=6,
        count_labs=7,
        action_date=dt.datetime(2024, 2, 20),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['marge_relationship'],
        action_by_user=relationships['marge_relationship'].caregiver.user,
        patient=relationships['marge_relationship'].patient,
        count_checkins=10,
        count_documents=11,
        count_educational_materials=12,
        count_questionnaires_complete=13,
        count_labs=14,
        action_date=dt.datetime(2024, 3, 20),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['bart_relationship'],
        action_by_user=relationships['bart_relationship'].caregiver.user,
        patient=relationships['bart_relationship'].patient,
        count_checkins=5,
        count_documents=6,
        count_educational_materials=7,
        count_questionnaires_complete=8,
        count_labs=9,
        action_date=dt.datetime(2024, 8, 20),
    )
    stats_factories.DailyUserPatientActivity(
        user_relationship_to_patient=relationships['lisa_relationship'],
        action_by_user=relationships['lisa_relationship'].caregiver.user,
        patient=relationships['lisa_relationship'].patient,
        count_checkins=7,
        count_documents=8,
        count_educational_materials=9,
        count_questionnaires_complete=10,
        count_labs=11,
        action_date=dt.datetime(2024, 8, 20),
    )

    annually_user_report = stats_queries.fetch_annually_user_pat_activity_log_report()
    assert annually_user_report == [
        {
            'year': dt.date(2024, 1, 1),
            'checkins_count': 25,
            'documents_count': 29,
            'educational_materials_count': 33,
            'completed_questionnaires_count': 37,
            'labs_count': 41,
        },
    ]


def _create_relationship_records() -> dict[str, Any]:
    """Create relationships for 4 patients.

    The records are created for Marge, Homer, Bart, and Lisa.

    Returns:
        dictionary with self relationships
    """
    marge_caregiver = caregiver_factories.CaregiverProfile(
        user__username='marge', legacy_id=1, user__last_login=timezone.now(),
    )
    homer_caregiver = caregiver_factories.CaregiverProfile(
        user__username='homer', legacy_id=2, user__last_login=timezone.now(),
    )
    bart_caregiver = caregiver_factories.CaregiverProfile(user__username='bart', legacy_id=3)
    lisa_caregiver = caregiver_factories.CaregiverProfile(user__username='lisa', legacy_id=4)

    marge_patient = patient_factories.Patient(legacy_id=51, ramq='TEST01161972')
    homer_patient = patient_factories.Patient(legacy_id=52, ramq='TEST01161973')
    bart_patient = patient_factories.Patient(legacy_id=53, ramq='TEST01161974')
    lisa_patient = patient_factories.Patient(legacy_id=54, ramq='TEST01161975')

    # marge
    marge_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=marge_patient,
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
    homer_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=patient_factories.Patient(legacy_id=52, ramq='TEST01161973'),
        caregiver=homer_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    homer_pending_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=homer_patient,
        caregiver=homer_caregiver,
        status=patient_models.RelationshipStatus.PENDING,
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
        patient=patient_factories.Patient(legacy_id=53, ramq='TEST01161974'),
        caregiver=bart_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    bart_expired_self_relationship = patient_factories.Relationship(
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
    lisa_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=patient_factories.Patient(legacy_id=54, ramq='TEST01161975'),
        caregiver=lisa_caregiver,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    lisa_pending_self_relationship = patient_factories.Relationship(
        type=patient_models.RelationshipType.objects.self_type(),
        patient=lisa_patient,
        caregiver=lisa_caregiver,
        status=patient_models.RelationshipStatus.PENDING,
    )

    return {
        'marge_relationship': marge_self_relationship,
        'homer_relationship': homer_self_relationship,
        'bart_relationship': bart_self_relationship,
        'lisa_relationship': lisa_self_relationship,
        'marge_homer_relationship': marge_homer_relationship,
        'homer_pending_relationship': homer_pending_self_relationship,
        'marge_bart_relationship': marge_bart_relationship,
        'bart_expired_relationship': bart_expired_self_relationship,
        'homer_lisa_relationship': homer_lisa_relationship,
        'lisa_pending_relationship': lisa_pending_self_relationship,
    }
