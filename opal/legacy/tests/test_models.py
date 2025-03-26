import pytest

from .. import factories

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_legacy_user_model() -> None:
    """Test LegacyUser model instantiation."""
    test_user = factories.LegacyUserFactory()
    test_user.full_clean()


def test_legacy_patient_model() -> None:
    """Test LegacyPatient model instantiation."""
    test_patient = factories.LegacyPatientFactory()
    test_patient.full_clean()


def test_legacy_notification_model() -> None:
    """Test legacy notification model."""
    test_notification = factories.LegacyNotificationFactory()
    test_notification.full_clean()


def test_legacy_appointment_model() -> None:
    """Test legacy appointment model."""
    test_appointment = factories.LegacyAppointmentFactory()
    test_appointment.full_clean()
