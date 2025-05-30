# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils import timezone

import pytest

from opal.patients.factories import Patient, Relationship
from opal.users.factories import Caregiver

from .. import factories
from ..models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity

pytestmark = pytest.mark.django_db()


def test_daily_patient_data_received_factory() -> None:
    """Ensure the `DailyPatientDataReceived` factory creates a valid model."""
    patient_data = factories.DailyPatientDataReceived.create()

    patient_data.full_clean()


def test_daily_user_app_activity_factory() -> None:
    """Ensure the `DailyUserAppActivity` factory creates a valid model."""
    patient_data = factories.DailyUserAppActivity.create()

    patient_data.full_clean()


def test_daily_user_patient_activity_factory() -> None:
    """Ensure the `DailyUserPatientActivity` factory creates a valid model."""
    patient_data = factories.DailyUserPatientActivity.create()

    patient_data.full_clean()


def test_daily_patient_data_received_str() -> None:
    """Ensure the `__str__` method is defined for the `DailyPatientDataReceived` model."""
    action_date = timezone.now()
    patient_data = DailyPatientDataReceived(
        patient=Patient.create(),
        action_date=action_date,
    )

    assert str(patient_data) == 'Simpson, Marge received data on {action_date}'.format(
        action_date=action_date.strftime('%Y-%m-%d'),
    )


def test_daily_user_patient_activity_str() -> None:
    """Ensure the `__str__` method is defined for the `DailyUserPatientActivity` model."""
    patient = Patient.create()
    patient_data = DailyUserPatientActivity(
        action_by_user=Caregiver.create(),
        patient=patient,
    )

    assert str(patient_data) == f'Daily activity by user Marge, Simpson on behalf of patient {patient}'


def test_daily_user_app_activity_str() -> None:
    """Ensure the `__str__` method is defined for the `DailyUserAppActivity` model."""
    caregiver = Caregiver.create()
    user_data = DailyUserAppActivity(
        action_by_user=caregiver,
    )

    assert str(user_data) == f'Daily activity by {caregiver.first_name}, {caregiver.last_name}'


def test_daily_user_app_activity_new_can_save() -> None:
    """Ensure a new `DailyUserAppActivity` instance can be saved."""
    patient_data = factories.DailyUserAppActivity.build(
        action_by_user=Caregiver.create(),
    )

    patient_data.save()


def test_daily_user_patient_activity_new_can_save() -> None:
    """Ensure a new `DailyUserPatientActivity` instance can be saved."""
    relationship = Relationship.create()

    patient_data = factories.DailyUserPatientActivity.build(
        user_relationship_to_patient=relationship,
        action_by_user=Caregiver.create(),
        patient=relationship.patient,
    )

    patient_data.save()


def test_daily_patient_data_received_new_can_save() -> None:
    """Ensure a new `DailyPatientDataReceived` instance can be saved."""
    patient = Patient.create()

    patient_data = factories.DailyPatientDataReceived.build(
        patient=patient,
    )

    patient_data.save()


def test_daily_user_app_activity_multiple_per_patient() -> None:
    """Ensure a relationship can have multiple `DailyUserAppActivity` records."""
    factories.DailyUserAppActivity.create(
        action_by_user=Caregiver.create(),
    )
    factories.DailyUserAppActivity.create(
        action_by_user=Caregiver.create(),
    )

    assert DailyUserAppActivity.objects.count() == 2


def test_daily_patient_data_received_multiple_per_patient() -> None:
    """Ensure a patient can have multiple `DailyPatientDataReceived` records."""
    patient = Patient.create()

    factories.DailyPatientDataReceived.create(patient=patient)
    factories.DailyPatientDataReceived.create(patient=patient)

    assert DailyPatientDataReceived.objects.count() == 2
