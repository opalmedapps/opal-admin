from datetime import datetime

import pytest

from .. import factories
from ..models import LegacyAnswerQuestionnaire

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
        'answer_questionnaire_ser_num',
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
