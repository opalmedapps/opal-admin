import re
from datetime import datetime

import pytest

from opal.caregivers import factories as caregiver_factories
from opal.patients import factories as patient_factories

from .. import factories
from ..models import LegacyAnswerQuestionnaire, LegacyQuestionnaire

pytestmark = pytest.mark.django_db(databases=['default', 'questionnaire'])


def test_get_questionnaire_databank_data() -> None:
    """Ensure questionnaire data for databank is returned and formatted correctly.

    Note that the test data returned by this query is dependent on
    what is hard coded in our test_QuestionnaireDB setup.
    See opal/tests/sql/test_QuestionnaireDB.sql
    """
    # Prepare patients and last cron run time
    non_consenting_patient = factories.LegacyQuestionnairePatientFactory(external_id=52)
    consenting_patient = factories.LegacyQuestionnairePatientFactory(external_id=51)
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
        assert 'consent' not in questionnaire_answer['questionnaire_title'].lower()
        assert re.search(r'\bmiddle\s+name\b', questionnaire_answer['question_text'], re.IGNORECASE) is None
        assert re.search(r'\bcity\s+of\s+birth\b', questionnaire_answer['question_text'], re.IGNORECASE) is None

    assert len(databank_data) == 7


def test_new_questionnaires_patient_caregiver() -> None:
    """Ensure LegacyQuestionnaireManager function 'new_questionnaires' is working.

    Get questionnaires  with respendonts 'Caregiver' and 'Patient'
    Get empty return with incorrect username
    """
    caregiver = caregiver_factories.Caregiver(username='test_new_questionnaires')
    caregiver_profile = caregiver_factories.CaregiverProfile(user=caregiver)
    legacy_patient = factories.LegacyQuestionnairePatientFactory()
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
    legacy_patient = factories.LegacyQuestionnairePatientFactory()
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
