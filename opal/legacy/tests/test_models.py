import pytest

from .. import factories

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_legacy_user_factory() -> None:
    """Test whether the factory creates a valid legacy user model instance."""
    test_user = factories.LegacyUserFactory()
    test_user.full_clean()


def test_legacy_patient_factory() -> None:
    """Test whether the factory creates a valid legacy patient model instance."""
    test_patient = factories.LegacyPatientFactory()
    test_patient.full_clean()


def test_legacy_patient_factory_multiple() -> None:
    """Test that the LegacyPatient factory gets an existing instance by patient ID."""
    test_patient = factories.LegacyPatientFactory()
    test_patient2 = factories.LegacyPatientFactory()

    assert test_patient == test_patient2


def test_legacy_notification_factory() -> None:
    """Test whether the factory creates a valid legacy notification model instance."""
    test_notification = factories.LegacyNotificationFactory()
    test_notification.full_clean()


def test_legacy_appointment_factory() -> None:
    """Test whether the factory creates a valid legacy appointment model instance."""
    test_appointment = factories.LegacyAppointmentFactory()
    test_appointment.full_clean()


def test_legacy_document_factory() -> None:
    """Test whether the factory creates a valid legacy document model instance."""
    test_document = factories.LegacyDocumentFactory()
    test_document.full_clean()


def test_legacy_txteammessage_factory() -> None:
    """Test whether the factory creates a valid legacy txteammessage model instance."""
    test_txteammessage = factories.LegacyTxTeamMessageFactory()
    test_txteammessage.full_clean()


def test_legacy_educationmaterial_factory() -> None:
    """Test whether the factory creates a valid legacy educational material model instance."""
    test_edumaterial = factories.LegacyEducationalMaterialFactory()
    test_edumaterial.full_clean()


def test_legacy_questionnaire_factory() -> None:
    """Test whether the factory creates a valid legacy questionnaire model instance."""
    test_questionnaire = factories.LegacyQuestionnaireFactory()
    test_questionnaire.full_clean()
