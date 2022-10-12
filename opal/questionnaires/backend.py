# flake8: noqa

import html
import logging

from django.conf import settings
from django.db import connections
from django.db.utils import DatabaseError

import datetime

from typing import Any

# Logger instance declared at the module level
logger = logging.getLogger(__name__)

test_accounts = settings.TEST_ACCOUNTS


def _getdescription(qid: int, langId: int) -> Any:
    with connections['QuestionnaireDB'].cursor() as c:
        c.execute(
            f'SELECT description FROM questionnaire WHERE ID = {qid}'
        )
        descriptionID = c.fetchone()[0]
        c.execute(
            f'SELECT content FROM dictionary WHERE contentId = {descriptionID} and languageId = {langId}'
        )
        description = c.fetchone()[0]
    return description


def dictfetchall(cursor: Any) -> Any:
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_all_questionnaire() -> Any:
    """Return list of non-test patient responded questionnaires from the DB"""
    # TODO REMOVE: Hardcode questionnaire list to allow testing
    return [{'ID': 11, 'name': 'Patient Satisfaction Questionnaire'}, {'ID': 12, 'name': 'Edmonton Symptom Assessment System'}, {'ID': 18, 'name': 'Breast Radiotherapy Symptoms'}]
    try:
        with connections['QuestionnaireDB'].cursor() as c:
            c.execute(f'SELECT DISTINCT questionnaireId FROM answer where deleted=0 and patientId not in {test_accounts}')
            aq = tuple([row[0] for row in c.fetchall()])
            c.execute(f'SELECT ID, getDisplayName(title, {2}) `name` FROM questionnaire WHERE ID in {aq}')
            qs = dictfetchall(c)
    except DatabaseError as err:
        logger.error(f'DatabaseError: No questionnaires found, are you sure you are connected to a production database? \n Error:  {err} ')
        return {}
    return qs


def get_questionnaire_detail(qid: int) -> Any:
    # TODO REMOVE for testing only
    return {'questionnaire': {'ID': 12, 'name': 'Edmonton Symptom Assessment System'}, 'patientIDs': [37, 47, 49, 59, 67, 94, 111, 120, 163, 171, 190, 211, 238, 251, 252, 253, 257, 273, 338, 339, 340, 342, 344, 380, 383, 384, 396,
399, 401, 407, 421, 449, 478, 479, 481, 482, 487, 513, 531, 578, 579, 611, 629, 664, 694, 695, 698, 727, 728, 775, 801, 870, 971, 1535], 'mindate': datetime.date(2019, 4, 10), 'maxdate': datetime.date(2022, 1, 13), 'questions': [{'questionId': 793, 'question': 'Please rate the following on a scale from 1 to 10: Drowsiness (feeling sleepy)', 'typeId': 2}, {'questionId': 794, 'question': 'Please rate the following on a scale from 1 to 10: Nausea', 'typeId': 2}, {'questionId': 795, 'question': 'Please rate the following on a scale from 1 to 10: Lack of appetite', 'typeId': 2}, {'questionId': 791, 'question': 'Please rate the following on a scale from 1 to 10: Pain', 'typeId': 2}, {'questionId': 796, 'question': 'Please rate the following on a scale from 1 to 10: Shortness of breath', 'typeId': 2}, {'questionId': 792, 'question': 'Please rate the following on a scale from 1 to 10: Tiredness (lack of energy)', 'typeId': 2}, {'questionId': 799, 'question': 'Please rate the following on a scale from 1 to 10: Wellbeing (how you feel overall)', 'typeId': 2}, {'questionId': 797, 'question': 'Please rate the following on a scale from 1 to 10: Depression (feeling sad)', 'typeId': 2}, {'questionId': 798, 'question': 'Please rate the following on a scale from 1 to 10: Anxiety (feeling nervous)', 'typeId': 2}], 'description': '<p><span style=\'font-size: 14px;float: none;\'>Patients sometimes report that they have the following symptoms or problems. Please indicate the extent to which you have experienced these symptoms or problems during the past week.</span><!--EndFragment--><br/><br/></p>'}
    with connections['QuestionnaireDB'].cursor() as c:
        c.execute(
            f'SELECT ID, getDisplayName(title, {2}) `name` FROM questionnaire WHERE ID = {qid}'
        )
        questionnaire = dictfetchall(c)

        c.execute(
            'DROP TABLE IF EXISTS`tempB`'
        )

        c.execute(
            f"""create table tempB(SELECT AQ.questionnaireId, date(AQ.creationDate) creationDate,
            date(AQ.lastUpdated) lastUpdated, AQ.patientId, A.questionId,
            getDisplayName(Q.question, {2}) `question`, A.typeId, A.ID AnswerID
            from answerQuestionnaire AQ, answerSection aSection, answer A, question Q
            where AQ.questionnaireId = {qid} and AQ.patientId not in {test_accounts} and AQ.`status` = 2
            and AQ.ID = aSection.answerQuestionnaireId and aSection.ID = A.answerSectionId and A.deleted = 0
            and A.answered = 1 and A.questionId = Q.ID) """
        )

        c.execute(f'SELECT DISTINCT patientId FROM tempB ')
        patientIDs = [row[0] for row in c.fetchall()]
        patientIDs.sort()

        c.execute(f'SELECT MIN(lastUpdated) FROM tempB ')
        mindate = c.fetchone()

        c.execute(f'SELECT MAX(lastUpdated) FROM tempB ')
        maxdate = c.fetchone()

        c.execute('SELECT DISTINCT questionId, question, typeId FROM tempB')
        questions = dictfetchall(c)

    description = _getdescription(qid, 2)
    description = html.unescape(description)

    return {
        'questionnaire': questionnaire[0],
        'patientIDs': patientIDs,
        'mindate': mindate[0],
        'maxdate': maxdate[0],
        'questions': questions,
        'description': description
    }
