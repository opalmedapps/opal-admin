# flake8: noqa

import datetime
import html
import logging
from typing import Any

from django.conf import settings
from django.db import connections
from django.db.utils import DatabaseError
from django.http.request import QueryDict

# Logger instance declared at the module level
logger = logging.getLogger(__name__)

test_accounts = settings.TEST_PATIENTS


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


def dictfetchall(cursor: Any) -> list[dict]:
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


def make_tempC(report_params: QueryDict) -> bool:
    """
    Query the QuestionnaireDB with the user's specific options for a questionnaire and store the results
    in the table tempC in QuestionnaireDB.

    :return: Boolean: successful query or not
    """
    qid = report_params.get('questionnaireid')
    pids = tuple(report_params.getlist('patientIDs'))
    qids = tuple(report_params.getlist('questionIDs'))
    startdate = report_params.get('start')
    enddate = report_params.get('end')

    # to avoid trailing comma for tuples with 1 item
    sql_pids = ', '.join(map(str, pids))
    sql_qids = ', '.join(map(str, qids))
    if qid and sql_pids and sql_qids and startdate and enddate:
        # TODO: testing only
        return True
        with connections['QuestionnaireDB'].cursor() as c:
            c.execute(
                'DROP TABLE IF EXISTS`temp`'
            )
            c.execute(
                'DROP TABLE IF EXISTS`tempA`'
            )
            c.execute(
                'DROP TABLE IF EXISTS`tempB`'
            )
            c.execute(
                'DROP TABLE IF EXISTS`tempC`'
            )

            c.execute(
                f"""create table tempA(SELECT Q.ID Questionnaire_ID, getDisplayName(Q.title, {2})
                Questionnaire_Title, S.ID Section_ID, qs.questionId, qs.`order`,
                getDisplayName(qq.question, {2}) Question_Title
                From questionnaire Q, section S, questionSection qs, question qq
                where Q.ID = {qid} and S.questionnaireId = Q.ID and qq.ID in ({sql_qids}) and qs.sectionId = S.ID
                and qq.ID = qs.questionId)
                """
            )
            c.execute(
                f"""create table tempB(SELECT AQ.questionnaireId, date(AQ.creationDate) creationDate,
                date(AQ.lastUpdated) lastUpdated, AQ.patientId, A.questionId,
                QuestionnaireDB.getDisplayName(Q.question, {2}) `question`, A.typeId, A.ID AnswerID
                from answerQuestionnaire AQ, answerSection aSection, answer A, question Q
                where AQ.questionnaireId = {qid} and AQ.patientId not in {test_accounts} and AQ.patientId in ({sql_pids})
                and AQ.lastUpdated and AQ.`status` = 2
                and cast(AQ.lastUpdated as date) BETWEEN '{startdate}' and '{enddate}'
                and AQ.ID = aSection.answerQuestionnaireId and aSection.ID = A.answerSectionId
                and A.deleted = 0 and A.answered = 1 and A.questionId = Q.ID)
                """
            )
            c.execute(
                """create table temp(SELECT A.Questionnaire_ID, A.Questionnaire_Title, A.Section_ID, A.order, B.*
                from tempA A, tempB B
                where A.questionId = B.questionId)
                """
            )
            c.execute('create index idx_A on temp (AnswerID)')
            c.execute('create index idx_B on temp (typeId)')
            c.execute(
                f"""create table tempC(SELECT A.*, answerTextBox.VALUE AS Answer
                FROM temp A, QuestionnaireDB.answerTextBox
                WHERE answerTextBox.answerId = A.AnswerID and A.typeId = 3
                UNION
                SELECT A.*, answerSlider.VALUE AS Answer
                FROM temp A, QuestionnaireDB.answerSlider
                WHERE answerSlider.answerId = A.AnswerID and A.typeId = 2
                UNION
                SELECT A.*, answerDate.VALUE AS Answer
                FROM temp A, QuestionnaireDB.answerDate
                WHERE answerDate.answerId = A.AnswerID and A.typeId = 7
                UNION
                SELECT A.*, answerTime.VALUE AS Answer
                FROM temp A, QuestionnaireDB.answerTime
                WHERE answerTime.answerId = A.AnswerID and A.typeId = 6
                UNION
                SELECT A.*, QuestionnaireDB.getDisplayName(rbOpt.description, {2}) AS Answer
                FROM temp A, QuestionnaireDB.answerRadioButton aRB, QuestionnaireDB.radioButtonOption rbOpt
                WHERE aRB.answerId = A.AnswerID AND rbOpt.ID = aRB.`value` and A.typeId = 4
                UNION
                Select A.*, QuestionnaireDB.getDisplayName(cOpt.description, {2}) AS Answer
                from temp A, QuestionnaireDB.answerCheckbox aC, QuestionnaireDB.checkboxOption cOpt
                where aC.answerId = A.AnswerID AND cOpt.ID = aC.`value` and A.typeId = 1
                UNION
                Select A.*, QuestionnaireDB.getDisplayName(lOpt.description, {2}) AS Answer
                from temp A, QuestionnaireDB.answerLabel aL, QuestionnaireDB.labelOption lOpt
                where aL.answerId = A.AnswerID AND lOpt.ID = aL.`value` and A.typeId = 5)
                """
            )
    else:
        return False
    return True


def get_tempC() -> list[dict]:
    """
    The query with the user's specific options for a questionnaire in make_tempC is stored in the table tempC
    in the QuestionnaireDB. This is a function to retrieve data from tempC that will be used for the reports.

    :return: list of all rows of the query as dictionaries
    """
    # TODO: remove testing only
    return [{'patient_id': 16, 'question_id': 859, 'question': 'Please enter any comments you have about the Opal app.  These can be comments about what you like, or suggestions about what could be added or improved.', 'answer': 'J aime bcp l App , j ai hâte de voir d autre fonctions qui seront disponible, diagnostic, notes du médecin etc..', 'creation_date': datetime.date(2018, 11, 25), 'last_updated': datetime.date(2018, 11, 25)}, {'patient_id': 17, 'question_id': 853, 'question': 'How useful is the Opal app?', 'answer': '4', 'creation_date': datetime.date(2018, 11, 25), 'last_updated': datetime.date(2018, 11, 25)}]
    with connections['QuestionnaireDB'].cursor() as c:
        c.execute(
            f'SELECT patientId, questionId, question, Answer, creationDate,	lastUpdated FROM tempC ORDER BY lastUpdated ASC'
        )
        q_dict = dictfetchall(c)
    return q_dict
