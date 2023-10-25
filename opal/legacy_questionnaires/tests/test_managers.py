from datetime import datetime

import pytest

from opal.caregivers import factories as caregiver_factories
from opal.patients import factories as patient_factories

from .. import factories
from ..models import LegacyAnswer, LegacyAnswerQuestionnaire, LegacyQuestionnaire

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


def test_get_questionnaire_databank_data() -> None:
    """Ensure questionnaire data for databank is returned and formatted correctly.

    Note that the test data returned by this query is dependent on
    what is hard coded in our test_QuestionnaireDB setup.
    See opal/tests/sql/test_QuestionnaireDB.sql
    """
    # Prepare patients and last cron run time
    non_consenting_patient = factories.LegacyPatientFactory(external_id=52)
    consenting_patient = factories.LegacyPatientFactory(external_id=51)
    last_cron_sync_time = datetime(2023, 1, 1, 0, 0, 5)

    # Fetch the data
    databank_data_empty = LegacyAnswerQuestionnaire.objects.get_databank_data_for_patient(
        patient_ser_num=non_consenting_patient.external_id,
        last_synchronized=last_cron_sync_time,
    )
    assert not databank_data_empty
    databank_data = LegacyAnswerQuestionnaire.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.external_id,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'answer_questionnaire_id',
        'creation_date',
        'questionnaire_id',
        'questionnaire_title',
        'question_id',
        'question_text',
        'question_display_order',
        'question_type_id',
        'question_type_text',
        'question_answer_id',
        'last_updated',
        'answer_value',
    }

    for questionnaire_answer in databank_data:
        assert questionnaire_answer['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(questionnaire_answer.keys()))

    assert len(databank_data) == 7


def test_new_questionnaires_patient_caregiver() -> None:
    """Ensure LegacyQuestionnaireManager function 'new_questionnaires' is working.

    Get questionnaires  with respendonts 'Caregiver' and 'Patient'
    Get empty return with incorrect username
    """
    caregiver = caregiver_factories.Caregiver(username='test_new_questionnaires')
    caregiver_profile = caregiver_factories.CaregiverProfile(user=caregiver)
    legacy_patient = factories.LegacyPatientFactory()
    patient = patient_factories.Patient(legacy_id=legacy_patient.external_id)
    relationship_type = patient_factories.RelationshipType(
        can_answer_questionnaire=True,
        role_type='GRDNCAREGIVER',
    )
    patient_factories.Relationship(
        type=relationship_type,
        caregiver=caregiver_profile,
        patient=patient,
    )

    # legacy factory instances
    legacy_dictionary = factories.LegacyDictionaryFactory(
        content='RESEARCH',
        content_id=1,
        language_id=2,
    )
    legacy_purpose = factories.LegacyPurposeFactory(title=legacy_dictionary, id=2)

    legacy_dictionary1 = factories.LegacyDictionaryFactory(
        content='Patient',
        content_id=3,
        language_id=2,
    )
    legacy_respondent1 = factories.LegacyRespondentFactory(title=legacy_dictionary1)
    legacy_questionnaire1 = factories.LegacyQuestionnaireFactory(
        purpose=legacy_purpose,
        respondent=legacy_respondent1,
    )
    legacy_questionnaire1 = factories.LegacyAnswerQuestionnaireFactory(
        questionnaire=legacy_questionnaire1,
        patient=legacy_patient,
    )

    legacy_dictionary2 = factories.LegacyDictionaryFactory(
        content='Caregiver',
        content_id=4,
        language_id=2,
    )
    legacy_respondent2 = factories.LegacyRespondentFactory(title=legacy_dictionary2)
    legacy_questionnaire2 = factories.LegacyQuestionnaireFactory(
        purpose=legacy_purpose,
        respondent=legacy_respondent2,
    )
    factories.LegacyAnswerQuestionnaireFactory(
        questionnaire=legacy_questionnaire2,
        patient=legacy_patient,
    )

    new_questionnaires = LegacyQuestionnaire.objects.new_questionnaires(
        legacy_patient.external_id,
        'test_new_questionnaires',
        legacy_purpose.id,
    )

    assert len(new_questionnaires) == 2

    new_questionnaires = LegacyQuestionnaire.objects.new_questionnaires(
        legacy_patient.external_id,
        'test_wrong_username',
        legacy_purpose.id,
    )

    assert not new_questionnaires


def test_new_questionnaires_return_empty_without_rependont_matching() -> None:
    """Ensure LegacyQuestionnaireManager function 'new_questionnaires' is working.

    Get empty questionnaires with unexpected respendonts
    """
    caregiver = caregiver_factories.Caregiver(username='test_new_questionnaires')
    caregiver_profile = caregiver_factories.CaregiverProfile(user=caregiver)
    legacy_patient = factories.LegacyPatientFactory()
    patient = patient_factories.Patient(legacy_id=legacy_patient.external_id)
    relationship_type = patient_factories.RelationshipType(
        can_answer_questionnaire=False,
        role_type='SELF',
    )
    patient_factories.Relationship(
        type=relationship_type,
        caregiver=caregiver_profile,
        patient=patient,
    )

    # legacy factory instances
    legacy_dictionary = factories.LegacyDictionaryFactory(
        content='RESEARCH',
        content_id=1,
        language_id=2,
    )
    legacy_purpose = factories.LegacyPurposeFactory(title=legacy_dictionary)

    legacy_dictionary1 = factories.LegacyDictionaryFactory(
        content='Patient',
        content_id=3,
        language_id=2,
    )
    legacy_respondent1 = factories.LegacyRespondentFactory(title=legacy_dictionary1)
    legacy_questionnaire1 = factories.LegacyQuestionnaireFactory(
        purpose=legacy_purpose,
        respondent=legacy_respondent1,
    )
    legacy_questionnaire1 = factories.LegacyAnswerQuestionnaireFactory(
        questionnaire=legacy_questionnaire1,
        patient=legacy_patient,
    )

    legacy_dictionary2 = factories.LegacyDictionaryFactory(
        content='Caregiver',
        content_id=4,
        language_id=2,
    )
    legacy_respondent2 = factories.LegacyRespondentFactory(title=legacy_dictionary2)
    legacy_questionnaire2 = factories.LegacyQuestionnaireFactory(
        purpose=legacy_purpose,
        respondent=legacy_respondent2,
    )
    factories.LegacyAnswerQuestionnaireFactory(
        questionnaire=legacy_questionnaire2,
        patient=legacy_patient,
    )

    new_questionnaires = LegacyQuestionnaire.objects.new_questionnaires(
        legacy_patient.external_id,
        'test_new_questionnaires',
        legacy_purpose.id,
    )

    assert not new_questionnaires


def test_get_guid_fields() -> None:  # noqa: WPS213
    """Test successful retrieval of the guid fields middle name and city of birth."""
    # Prepare all data for consent and guid generation
    consenting_patient = factories.LegacyPatientFactory(external_id=51)
    # Questionnaire content
    middle_name_content = factories.LegacyDictionaryFactory(content_id=22222, content='Middle name', language_id=2)
    middle_name_question = factories.LegacyQuestionFactory(display=middle_name_content)
    cob_content = factories.LegacyDictionaryFactory(content_id=33333, content='City of birth', language_id=2)
    cob_question = factories.LegacyQuestionFactory(display=cob_content)
    consent_purpose = factories.LegacyPurposeFactory(id=4)
    questionnaire_title = factories.LegacyDictionaryFactory(
        content_id=44444,
        content='Databank Consent Questionnaire',
        language_id=2,
    )
    consent_questionnaire = factories.LegacyQuestionnaireFactory(purpose=consent_purpose, title=questionnaire_title)
    section = factories.LegacySectionFactory(questionnaire=consent_questionnaire)
    factories.LegacyQuestionSectionFactory(question=middle_name_question, section=section)
    factories.LegacyQuestionSectionFactory(question=cob_question, section=section)
    # Answer data
    answer_questionnaire = factories.LegacyAnswerQuestionnaireFactory(
        questionnaire=consent_questionnaire,
        patient=consenting_patient,
    )
    answer_section = factories.LegacyAnswerSectionFactory(answer_questionnaire=answer_questionnaire, section=section)
    cob_answer = factories.LegacyAnswerFactory(
        question=cob_question,
        answer_section=answer_section,
        patient=consenting_patient,
        questionnaire=consent_questionnaire,
    )
    middle_name_answer = factories.LegacyAnswerFactory(
        question=middle_name_question,
        answer_section=answer_section,
        patient=consenting_patient,
        questionnaire=consent_questionnaire,
    )
    factories.LegacyAnswerTextBoxFactory(answer=cob_answer, value='Montreal')
    factories.LegacyAnswerTextBoxFactory(answer=middle_name_answer, value='Juliet')

    results = LegacyAnswer.objects.get_guid_fields(consenting_patient.external_id)
    assert len(results) == 2
    for questionanswer in results:
        question_text = questionanswer['question_text']
        answer_text = questionanswer['answer_text']
        assert question_text in {'City of birth', 'Middle name'}
        if question_text == 'City of birth':
            assert answer_text == 'Montreal'
        elif question_text == 'Middle name':
            assert answer_text == 'Juliet'


def test_guid_field_answers_missing() -> None:
    """Test that the response is empty if no question answers have been saved."""
    consenting_patient = factories.LegacyPatientFactory(external_id=51)
    results = LegacyAnswer.objects.get_guid_fields(consenting_patient.external_id)
    assert not results
