import pytest

from .. import factories

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


def test_legacy_dictionary_factory() -> None:
    """Test whether the factory creates a valid legacy dictionary model instance."""
    test_dictionary = factories.LegacyDictionaryFactory()
    test_dictionary.full_clean()


def test_legacy_purpose_factory() -> None:
    """Test whether the factory creates a valid legacy purpose model instance."""
    test_purpose = factories.LegacyPurposeFactory()
    test_purpose.full_clean()


def test_legacy_questionnaire_factory() -> None:
    """Test whether the factory creates a valid legacy questionnaire model instance."""
    test_questionnaire = factories.LegacyQuestionnaireFactory()
    test_questionnaire.full_clean()


def test_legacy_patient_factory() -> None:
    """Test whether the factory creates a valid legacy patient model instance."""
    test_patient = factories.LegacyPatientFactory()
    test_patient.full_clean()


def test_legacy_answerquestionnaire_factory() -> None:
    """Test whether the factory creates a valid legacy answerquestionnaire model instance."""
    test_answerquestionnaire = factories.LegacyAnswerQuestionnaireFactory()
    test_answerquestionnaire.full_clean()
