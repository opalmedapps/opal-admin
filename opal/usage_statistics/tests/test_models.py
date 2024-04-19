from django.utils import timezone

import pytest

from opal.patients.factories import Patient, Relationship
from opal.users.factories import Caregiver

from .. import factories
from ..models import DailyPatientDataReceived, DailyUserAppActivity

pytestmark = pytest.mark.django_db()


def test_daily_patient_data_received_factory() -> None:
    """Ensure the `DailyPatientDataReceived` factory creates a valid model."""
    patient_data = factories.DailyPatientDataReceived()

    patient_data.full_clean()


def test_daily_user_app_activity_factory() -> None:
    """Ensure the `DailyUserAppActivity` factory creates a valid model."""
    patient_data = factories.DailyUserAppActivity()

    patient_data.full_clean()


def test_daily_patient_data_received_str() -> None:
    """Ensure the `__str__` method is defined for the `DailyPatientDataReceived` model."""
    date_added = timezone.now()
    patient_data = DailyPatientDataReceived(
        patient=Patient(),
        date_added=date_added,
    )

    assert str(patient_data) == 'Simpson, Marge received data on {date_added}'.format(
        date_added=date_added.strftime('%Y-%m-%d'),
    )


def test_daily_user_app_activity_str_no_patient() -> None:
    """Ensure the `__str__` can handle empty patient field."""
    patient_data = DailyUserAppActivity(
        action_by_user=Caregiver(),
    )

    assert str(patient_data) == 'Daily activity by Marge, Simpson'


def test_daily_user_app_activity_str() -> None:
    """Ensure the `__str__` method is defined for the `DailyUserAppActivity` model."""
    patient = Patient()
    patient_data = DailyUserAppActivity(
        action_by_user=Caregiver(),
        patient=patient,
    )

    assert str(patient_data) == 'Daily activity by user Marge, Simpson in the chart of patient {patient}'.format(
        patient=patient,
    )


def test_daily_user_app_activity_new_can_save() -> None:
    """Ensure a new `DailyUserAppActivity` instance can be saved."""
    relationship = Relationship()

    patient_data = factories.DailyUserAppActivity.build(
        user_relationship_to_patient=relationship,
        action_by_user=relationship.caregiver.user,
        patient=relationship.patient,
    )

    patient_data.save()


def test_daily_patient_data_received_new_can_save() -> None:
    """Ensure a new `DailyPatientDataReceived` instance can be saved."""
    patient = Patient()

    patient_data = factories.DailyPatientDataReceived.build(
        patient=patient,
    )

    patient_data.save()


def test_daily_user_app_activity_multiple_per_patient() -> None:
    """Ensure a relationship can have multiple `DailyUserAppActivity` records."""
    relationship = Relationship()

    factories.DailyUserAppActivity(
        user_relationship_to_patient=relationship,
        action_by_user=relationship.caregiver.user,
        patient=relationship.patient,
    )
    factories.DailyUserAppActivity(
        user_relationship_to_patient=relationship,
        action_by_user=relationship.caregiver.user,
        patient=relationship.patient,
    )

    assert DailyUserAppActivity.objects.count() == 2


def test_daily_patient_data_received_multiple_per_patient() -> None:
    """Ensure a patient can have multiple `DailyPatientDataReceived` records."""
    patient = Patient()

    factories.DailyPatientDataReceived(patient=patient)
    factories.DailyPatientDataReceived(patient=patient)

    assert DailyPatientDataReceived.objects.count() == 2
