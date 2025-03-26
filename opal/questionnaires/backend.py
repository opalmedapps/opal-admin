"""This file contains SQL queries for the ePRO reporting tool."""
import html
import logging

from django.conf import settings
from django.db import connections
from django.db.backends.utils import CursorWrapper
from django.db.utils import DatabaseError
from django.http.request import QueryDict

# Logger instance declared at the module level
logger = logging.getLogger(__name__)

if settings.DEBUG:
    test_accounts = ('')
else:
    test_accounts = ', '.join(map(str, settings.TEST_PATIENTS))


def _get_description(qid: int, lang_id: int) -> str:
    """Get detailed description for selected questionnaire.

    Args:
        qid: Questionnaire id.
        lang_id: requesting user language preference.

    Returns:
        description
    """
    with connections['questionnaire'].cursor() as conn:
        conn.execute(
            'SELECT description FROM questionnaire WHERE ID = %s', [qid],
        )
        description_id = conn.fetchone()[0]
        conn.execute(
            'SELECT content FROM dictionary WHERE contentId = %s and languageId = %s', [description_id, lang_id],
        )
        description = str(conn.fetchone()[0])
    return description


def fetch_all_as_dict(cursor: CursorWrapper) -> list[dict]:
    """Return all rows from a cursor as a dict.

    Args:
        cursor: Database connection.

    Returns:
        dictionary list for query.

    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_all_questionnaires(lang_id: int) -> list[dict]:
    """Get list of questionnaires which have non-zero number of responses.

    Args:
        lang_id: requesting user's language preference.

    Returns:
        dictionary list for the query.
    """
    try:
        with connections['questionnaire'].cursor() as conn:
            conn.execute(
                'SELECT DISTINCT questionnaireId FROM answer where deleted=0 and patientId not in (%s)',
                [test_accounts],
            )
            aq = tuple([row[0] for row in conn.fetchall()])
            conn.execute(
                'SELECT ID, getDisplayName(title, %s) `name` FROM questionnaire WHERE ID in %s',
                [lang_id, aq],
            )
            qs = fetch_all_as_dict(conn)
    except DatabaseError as err:
        logger.error(f'DatabaseError: No questionnaires found, are you sure you are connected to a production database? \n Error:  {err} ')  # noqa: E501
        return [{}]
    return qs


def get_questionnaire_detail(qid: int, lang_id: int) -> dict:  # noqa: WPS210, WPS213
    """Get details for desired questionnaire (questions, patients, dates).

    Args:
        qid: questionnaire id.
        lang_id: requesting user's language preference.

    Returns:
        dictionary list for the query.
    """
    with connections['questionnaire'].cursor() as conn:
        conn.execute(
            'SELECT ID, getDisplayName(title, %s) `name` FROM questionnaire WHERE ID = %s', [lang_id, qid],
        )
        questionnaire = fetch_all_as_dict(conn)

        conn.execute('DROP TABLE IF EXISTS`tempB`')
        conn.execute(
            """create table tempB(SELECT AQ.questionnaireId, date(AQ.creationDate) creationDate,
            date(AQ.lastUpdated) lastUpdated, AQ.patientId, A.questionId,
            getDisplayName(Q.question, %s) `question`, A.typeId, A.ID AnswerID
            from answerQuestionnaire AQ, answerSection aSection, answer A, question Q
            where AQ.questionnaireId = %s and AQ.patientId not in (%s) and AQ.`status` = 2
            and AQ.ID = aSection.answerQuestionnaireId and aSection.ID = A.answerSectionId and A.deleted = 0
            and A.answered = 1 and A.questionId = Q.ID) """, [lang_id, qid, test_accounts],
        )

        conn.execute('SELECT DISTINCT patientId FROM tempB')
        patient_ids = [row[0] for row in conn.fetchall()]
        patient_ids.sort()

        conn.execute('SELECT MIN(lastUpdated) FROM tempB')
        mindate = conn.fetchone()

        conn.execute('SELECT MAX(lastUpdated) FROM tempB')
        maxdate = conn.fetchone()

        conn.execute('SELECT DISTINCT questionId, question, typeId FROM tempB')
        questions = fetch_all_as_dict(conn)

    description = _get_description(qid, lang_id)
    description = html.unescape(description)

    return {
        'questionnaire': questionnaire[0],
        'patientIDs': patient_ids,
        'mindate': mindate[0],
        'maxdate': maxdate[0],
        'questions': questions,
        'description': description,
    }


def make_temp_tables(report_params: QueryDict, lang_id: int) -> bool:  # noqa: WPS210, WPS213
    """Query the QuestionnaireDB with the user's specific options & generate tables.

    Args:
        report_params: user options
        lang_id: int for english or french

    Returns:
        successful query or not
    """
    qid = report_params.get('questionnaireid')
    pids = tuple(report_params.getlist('patientIDs'))
    qids = tuple(report_params.getlist('questionIDs'))
    startdate = report_params.get('start')
    enddate = report_params.get('end')

    # to avoid trailing comma for tuples with 1 item
    sql_pids = ', '.join(map(str, pids))
    sql_qids = ', '.join(map(str, qids))

    if all([qid, pids, qids, startdate, enddate]):
        with connections['questionnaire'].cursor() as conn:
            conn.execute(
                'DROP TABLE IF EXISTS`temp`',
            )
            conn.execute(
                'DROP TABLE IF EXISTS`tempA`',
            )
            conn.execute(
                'DROP TABLE IF EXISTS`tempB`',
            )
            conn.execute(
                'DROP TABLE IF EXISTS`tempC`',
            )

            conn.execute(
                """create table tempA(SELECT Q.ID Questionnaire_ID, getDisplayName(Q.title, %s)
                Questionnaire_Title, S.ID Section_ID, qs.questionId, qs.`order`,
                getDisplayName(qq.question, %s) Question_Title
                From questionnaire Q, section S, questionSection qs, question qq
                where Q.ID = %s and S.questionnaireId = Q.ID and qq.ID in (%s) and qs.sectionId = S.ID
                and qq.ID = qs.questionId)
                """, [lang_id, lang_id, qid, sql_qids],
            )
            conn.execute(
                """create table tempB(SELECT AQ.questionnaireId, date(AQ.creationDate) creationDate,
                date(AQ.lastUpdated) lastUpdated, AQ.patientId, A.questionId,
                getDisplayName(Q.question, %s) `question`, A.typeId, A.ID AnswerID
                from answerQuestionnaire AQ, answerSection aSection, answer A, question Q
                where AQ.questionnaireId = %s and AQ.patientId not in (%s) and AQ.patientId in (%s)
                and AQ.lastUpdated and AQ.`status` = 2
                and cast(AQ.lastUpdated as date) BETWEEN %s and %s
                and AQ.ID = aSection.answerQuestionnaireId and aSection.ID = A.answerSectionId
                and A.deleted = 0 and A.answered = 1 and A.questionId = Q.ID)
                """, [lang_id, qid, test_accounts, sql_pids, startdate, enddate],
            )
            conn.execute(
                """create table temp(SELECT A.Questionnaire_ID, A.Questionnaire_Title, A.Section_ID, A.order, B.*
                from tempA A, tempB B
                where A.questionId = B.questionId)
                """,
            )
            conn.execute('create index idx_A on temp (AnswerID)')
            conn.execute('create index idx_B on temp (typeId)')
            conn.execute(
                """create table tempC(SELECT A.*, answerTextBox.VALUE AS Answer
                FROM temp A, answerTextBox
                WHERE answerTextBox.answerId = A.AnswerID and A.typeId = 3
                UNION
                SELECT A.*, answerSlider.VALUE AS Answer
                FROM temp A, answerSlider
                WHERE answerSlider.answerId = A.AnswerID and A.typeId = 2
                UNION
                SELECT A.*, answerDate.VALUE AS Answer
                FROM temp A, answerDate
                WHERE answerDate.answerId = A.AnswerID and A.typeId = 7
                UNION
                SELECT A.*, answerTime.VALUE AS Answer
                FROM temp A, answerTime
                WHERE answerTime.answerId = A.AnswerID and A.typeId = 6
                UNION
                SELECT A.*, getDisplayName(rbOpt.description, %s) AS Answer
                FROM temp A, answerRadioButton aRB, radioButtonOption rbOpt
                WHERE aRB.answerId = A.AnswerID AND rbOpt.ID = aRB.`value` and A.typeId = 4
                UNION
                Select A.*, getDisplayName(cOpt.description, %s) AS Answer
                from temp A, answerCheckbox aC, checkboxOption cOpt
                where aC.answerId = A.AnswerID AND cOpt.ID = aC.`value` and A.typeId = 1
                UNION
                Select A.*, getDisplayName(lOpt.description, %s) AS Answer
                from temp A, answerLabel aL, labelOption lOpt
                where aL.answerId = A.AnswerID AND lOpt.ID = aL.`value` and A.typeId = 5)
                """, [lang_id, lang_id, lang_id],
            )
    else:
        return False
    return True


def get_temp_table() -> list[dict]:
    """Retrieve the previously generated report in the temporary table.

    Returns:
        List of all rows of the query as dictionaries.
    """
    with connections['questionnaire'].cursor() as conn:
        conn.execute(
            """
            SELECT patientId as patient_id, questionId as question_id,
            question, Answer as answer, creationDate as creation_date,
            lastUpdated as last_updated
            FROM tempC
            ORDER BY last_updated ASC
            """,
        )
        q_dict = fetch_all_as_dict(conn)
    return q_dict
