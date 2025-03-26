import datetime as dt

from django.utils import timezone

import pytest

from opal.caregivers import factories as caregiver_factories
from opal.caregivers import models as caregiver_models
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.usage_statistics import queries as stats_queries

pytestmark = pytest.mark.django_db(databases=['default'])


def test_empty_fetch_population_summary() -> None:
    """Ensure fetch_population_summary() query can return an empty result without errors."""
    population_summary = stats_queries.fetch_population_summary()
    assert population_summary == {
        'user_signed_up': 0,
        'incomplete_registration': 0,
        'completed_registration': 0,
        'english': 0,
        'french': 0,
        'deceased': 0,
        'male': 0,
        'female': 0,
        'other_sex': 0,
        'unknown_sex': 0,
        'full_access': 0,
        'limit_access': 0,
    }


def test_fetch_population_summary() -> None:  # noqa: WPS213
    """Ensure fetch_population_summary() query successfully returns population statistics."""
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

    caregiver_factories.RegistrationCode(
        code='marge_code',
        relationship=marge_self_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='marge_homer',
        relationship=marge_homer_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='homer_self1',
        relationship=homer_first_self_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.BLOCKED,
    )
    caregiver_factories.RegistrationCode(
        code='homer_self2',
        relationship=homer_second_self_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='marge_bart',
        relationship=marge_bart_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='bart_self',
        relationship=bart_self_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='homer_lisa',
        relationship=homer_lisa_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='lisa_self1',
        relationship=lisa_first_self_relationship,
        created_at=timezone.now().date() - dt.timedelta(days=1),
        status=caregiver_models.RegistrationCodeStatus.REGISTERED,
    )
    caregiver_factories.RegistrationCode(
        code='lisa_self2',
        relationship=lisa_second_self_relationship,
        created_at=timezone.now().date(),
        status=caregiver_models.RegistrationCodeStatus.NEW,
    )

    population_summary = stats_queries.fetch_population_summary()
    assert population_summary == {
        'user_signed_up': 4,
        'incomplete_registration': 2,
        'completed_registration': 7,
        'english': 9,
        'french': 0,
        'deceased': 0,
        'male': 9,
        'female': 0,
        'other_sex': 0,
        'unknown_sex': 0,
        'full_access': 9,
        'limit_access': 0,
    }
