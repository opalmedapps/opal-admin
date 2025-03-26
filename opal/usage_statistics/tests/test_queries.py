import datetime as dt

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
        user__username='marge',
        legacy_id=1,
    )
    homer_caregiver = caregiver_factories.CaregiverProfile(
        user__username='homer',
        legacy_id=2,
    )
    bart_caregiver = caregiver_factories.CaregiverProfile(
        user__username='bart',
        legacy_id=3,
    )
    lisa_caregiver = caregiver_factories.CaregiverProfile(
        user__username='lisa',
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


def test_empty_logins_summary() -> None:
    """Ensure fetch_logins_summary() query can return an empty result without errors."""
    logins_summary = stats_queries.fetch_logins_summary(
        start_date=timezone.now().today(),
        end_date=timezone.now().today(),
    )
    assert not logins_summary


def test_fetch_logins_summary_by_date() -> None:
    """Ensure fetch_logins_summary() query successfully aggregates login statistics grouped by date."""
    marge_caregiver = caregiver_factories.CaregiverProfile(
        user__username='marge',
        legacy_id=1,
    )
    homer_caregiver = caregiver_factories.CaregiverProfile(
        user__username='homer',
        legacy_id=2,
    )
    bart_caregiver = caregiver_factories.CaregiverProfile(
        user__username='bart',
        legacy_id=3,
    )
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
    marge_caregiver = caregiver_factories.CaregiverProfile(
        user__username='marge',
        legacy_id=1,
    )
    homer_caregiver = caregiver_factories.CaregiverProfile(
        user__username='homer',
        legacy_id=2,
    )
    bart_caregiver = caregiver_factories.CaregiverProfile(
        user__username='bart',
        legacy_id=3,
    )
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
        action_by_user=homer_caregiver.user,
        count_logins=6,
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
            'total_logins': 12,
            'unique_user_logins': 3,
            'avg_logins_per_user': 4.0,
        },
        {
            'month': dt.date(2024, 3, 1),
            'total_logins': 24,
            'unique_user_logins': 3,
            'avg_logins_per_user': 8.0,
        },
    ]


def test_fetch_logins_summary_by_year() -> None:
    """Ensure fetch_logins_summary() query successfully aggregates login statistics grouped by year."""
    marge_caregiver = caregiver_factories.CaregiverProfile(
        user__username='marge',
        legacy_id=1,
    )
    homer_caregiver = caregiver_factories.CaregiverProfile(
        user__username='homer',
        legacy_id=2,
    )
    bart_caregiver = caregiver_factories.CaregiverProfile(
        user__username='bart',
        legacy_id=3,
    )
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
        action_by_user=marge_caregiver.user,
        count_logins=10,
        action_date=dt.date(2022, 4, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=homer_caregiver.user,
        count_logins=9,
        action_date=dt.date(2022, 3, 3),
    )
    stats_factories.DailyUserAppActivity(
        action_by_user=bart_caregiver.user,
        count_logins=5,
        action_date=dt.date(2022, 2, 1),
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
            'total_logins': 12,
            'unique_user_logins': 3,
            'avg_logins_per_user': 4.0,
        },
        {
            'year': dt.date(2022, 1, 1),
            'total_logins': 24,
            'unique_user_logins': 3,
            'avg_logins_per_user': 8.0,
        },
    ]
