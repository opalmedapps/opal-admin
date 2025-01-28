import pytest

from .. import factories

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


def test_legacy_definition_factory() -> None:
    """Test whether the factory creates a valid legacy definition table model instance."""
    test_deftable = factories.LegacyDefinitionTableFactory()
    test_deftable.full_clean()


def test_legacy_dictionary_factory() -> None:
    """Test whether the factory creates a valid legacy dictionary model instance."""
    test_dictionary = factories.LegacyDictionaryFactory()
    test_dictionary.full_clean()


def test_legacy_purpose_factory() -> None:
    """Test whether the factory creates a valid legacy purpose model instance."""
    test_purpose = factories.LegacyPurposeFactory()
    test_purpose.full_clean()


def test_legacy_respondent_factory() -> None:
    """Test whether the factory creates a valid legacy respondent model instance."""
    test_respondent = factories.LegacyRespondentFactory()
    test_respondent.full_clean()


def test_legacy_questionnaire_factory() -> None:
    """Test whether the factory creates a valid legacy questionnaire model instance."""
    test_questionnaire = factories.LegacyQuestionnaireFactory()
    test_questionnaire.full_clean()


def test_legacy_patient_factory() -> None:
    """Test whether the factory creates a valid legacy patient model instance."""
    test_patient = factories.LegacyQuestionnairePatientFactory()
    test_patient.full_clean()


def test_legacy_answerquestionnaire_factory() -> None:
    """Test whether the factory creates a valid legacy answerquestionnaire model instance."""
    test_answerquestionnaire = factories.LegacyAnswerQuestionnaireFactory()
    test_answerquestionnaire.full_clean()


def test_legacy_language_factory() -> None:
    """Test whether the factory creates a valid legacy language model instance."""
    test_language = factories.LegacyLanguageFactory()
    test_language.full_clean()


def test_legacy_checkboxoption_factory() -> None:
    """Test whether the factory creates a valid LegacyCheckboxOptionFactory model instance."""
    test_checkboxoption = factories.LegacyCheckboxOptionFactory()
    test_checkboxoption.full_clean()


def test_legacy_label_factory() -> None:
    """Test whether the factory creates a valid LegacyLabelFactory model instance."""
    test_label = factories.LegacyLabelFactory()
    test_label.full_clean()


def test_checkbox_factory() -> None:
    """Test whether the factory creates a valid LegacyCheckbox model instance."""
    test_checkbox = factories.LegacyCheckboxFactory()
    test_checkbox.full_clean()


def test_radio_button_factory() -> None:
    """Test whether the factory creates a valid LegacyRadioButton model instance."""
    test_rb = factories.LegacyRadioButtonFactory()
    test_rb.full_clean()


def test_legacy_labeloption_factory() -> None:
    """Test whether the factory creates a valid LegacyLabelOptionFactory model instance."""
    test_labeloption = factories.LegacyLabelOptionFactory()
    test_labeloption.full_clean()


def test_legacy_radiobuttonoption_factory() -> None:
    """Test whether the factory creates a valid LegacyRadioButtonOptionFactory model instance."""
    test_radiobuttonoption = factories.LegacyRadioButtonOptionFactory()
    test_radiobuttonoption.full_clean()


def test_legacy_section_factory() -> None:
    """Test whether the factory creates a valid LegacySectionFactory model instance."""
    test_section = factories.LegacySectionFactory()
    test_section.full_clean()


def test_legacy_type_factory() -> None:
    """Test whether the factory creates a valid LegacyTypeFactory model instance."""
    test_type = factories.LegacyTypeFactory()
    test_type.full_clean()


def test_legacy_question_factory() -> None:
    """Test whether the factory creates a valid LegacyQuestionFactory model instance."""
    test_question = factories.LegacyQuestionFactory()
    test_question.full_clean()


def test_legacy_questionsection_factory() -> None:
    """Test whether the factory creates a valid LegacyQuestionSectionFactory model instance."""
    test_questionsection = factories.LegacyQuestionSectionFactory()
    test_questionsection.full_clean()


def test_legacy_answersection_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerSectionFactory model instance."""
    test_answersection = factories.LegacyAnswerSectionFactory()
    test_answersection.full_clean()


def test_legacy_answer_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerFactory model instance."""
    test_answer = factories.LegacyAnswerFactory()
    test_answer.full_clean()


def test_legacy_answerslider_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerSliderFactory model instance."""
    test_answerslider = factories.LegacyAnswerSliderFactory()
    test_answerslider.full_clean()


def test_legacy_answertextbox_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerTextBoxFactory model instance."""
    test_answertextbox = factories.LegacyAnswerTextBoxFactory()
    test_answertextbox.full_clean()


def test_legacy_answertime_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerTimeFactory model instance."""
    test_answertime = factories.LegacyAnswerTimeFactory()
    test_answertime.full_clean()


def test_legacy_answerlabel_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerLabelFactory model instance."""
    test_answerlabel = factories.LegacyAnswerLabelFactory()
    test_answerlabel.full_clean()


def test_legacy_answerradiobutton_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerRadioButtonFactory model instance."""
    test_answerradiobutton = factories.LegacyAnswerRadioButtonFactory()
    test_answerradiobutton.full_clean()


def test_legacy_answercheckbox_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerCheckboxFactory model instance."""
    test_answercheckbox = factories.LegacyAnswerCheckboxFactory()
    test_answercheckbox.full_clean()


def test_legacy_answerdate_factory() -> None:
    """Test whether the factory creates a valid LegacyAnswerDateFactory model instance."""
    test_answerdate = factories.LegacyAnswerDateFactory()
    test_answerdate.full_clean()
