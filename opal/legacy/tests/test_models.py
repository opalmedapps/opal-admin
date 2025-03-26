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


def test_legacy_alias_factory() -> None:
    """Test whether the factory creates a valid legacy alias model instance."""
    test_alias = factories.LegacyAliasFactory()
    test_alias.full_clean()


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


def test_legacy_announcement_factory() -> None:
    """Test whether the factory creates a valid legacy announcement model instance."""
    test_announcement = factories.LegacyAnnouncementFactory()
    test_announcement.full_clean()


def test_legacy_post_control_factory() -> None:
    """Test whether the factory creates a valid legacy postControl model instance."""
    test_post_control = factories.LegacyPostcontrolFactory()
    test_post_control.full_clean()


def test_legacy_source_database_factory() -> None:
    """Test whether the factory creates a valid legacy SourceDatabase model instance."""
    test_source_database = factories.LegacySourceDatabaseFactory()
    test_source_database.full_clean()


def test_legacy_diagnosis_factory() -> None:
    """Test whether the factory creates a valid legacy Diagnosis model instance."""
    test_diagnosis = factories.LegacyDiagnosisFactory()
    test_diagnosis.full_clean()


def test_legacy_diagnosis_translation_factory() -> None:
    """Test whether the factory creates a valid legacy DiagnosisTranslation model instance."""
    test_diagnosis_translation = factories.LegacyDiagnosisTranslationFactory()
    test_diagnosis_translation.full_clean()


def test_legacy_diagnosis_code_factory() -> None:
    """Test whether the factory creates a valid legacy DiagnosisCode model instance."""
    test_diagnosis_code = factories.LegacyDiagnosisCodeFactory()
    test_diagnosis_code.full_clean()


def test_legacy_test_result_factory() -> None:
    """Test whether the factory creates a valid legacy TestResult model instance."""
    test_test_result = factories.LegacyTestResultFactory()
    test_test_result.full_clean()


def test_legacy_test_result_control_factory() -> None:
    """Test whether the factory creates a valid legacy TestResultControl model instance."""
    test_test_result_control = factories.LegacyTestResultControlFactory()
    test_test_result_control.full_clean()


def test_legacy_patient_test_result_factory() -> None:
    """Test whether the factory creates a valid legacy PatientTestResult model instance."""
    test_test_patient_result = factories.LegacyPatientTestResultFactory()
    test_test_patient_result.full_clean()


def test_legacy_test_group_expression() -> None:
    """Test whether the factory creates a valid legacy TestGroupExpression model instance."""
    test_test_group_expression = factories.LegacyTestGroupExpressionFactory()
    test_test_group_expression.full_clean()


def test_legacy_test_expression() -> None:
    """Test whether the factory creates a valid legacy TestExpression model instance."""
    test_test_expression = factories.LegacyTestExpressionFactory()
    test_test_expression.full_clean()


def test_legacy_test_control() -> None:
    """Test whether the factory creates a valid legacy TestControl model instance."""
    test_test_control = factories.LegacyTestControlFactory()
    test_test_control.full_clean()


def test_legacy_oauser() -> None:
    """Test whether the factory creates a valid legacy OAUser model instance."""
    test_oauser = factories.LegacyOAUserFactory()
    test_oauser.full_clean()


def test_legacy_oarole() -> None:
    """Test whether the factory creates a valid legacy oaRole model instance."""
    test_oarole = factories.LegacyOAUserFactory()
    test_oarole.full_clean()


def test_legacy_oauserrole() -> None:
    """Test whether the factory creates a valid legacy oaUserRole model instance."""
    test_oauserrole = factories.LegacyOAUserRoleFactory()
    test_oauserrole.full_clean()


def test_legacy_module() -> None:
    """Test whether the factory creates a valid legacy module model instance."""
    test_module = factories.LegacyModuleFactory()
    test_module.full_clean()


def test_legacy_oarolemodule() -> None:
    """Test whether the factory creates a valid legacy OARoleModule model instance."""
    test_oarolemodule = factories.LegacyOARoleModuleFactory()
    test_oarolemodule.full_clean()
