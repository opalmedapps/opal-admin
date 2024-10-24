-- Temp details table just contains questionnaire details plus the answer ids, not the answer values themselves
DROP TABLE IF EXISTS `tempAnswerDetails`;
CREATE TEMPORARY TABLE tempAnswerDetails(
	SELECT
		AQ.ID AS answer_questionnaire_id,
	   AQ.creationDate AS creation_date,
		qstnr.ID as questionnaire_id,
	   getDisplayName(qstnr.title, 2) AS questionnaire_title,
	   A.questionId AS question_id,
	   getDisplayName(Q.question, 2) AS question_text,
	   qs.`order` AS question_display_order,
	   A.typeId AS question_type_id,
      d.content AS question_type_text,
	   A.ID as question_answer_id,
	   AQ.lastUpdated AS last_updated
	FROM
	   answerQuestionnaire AQ,
	   dictionary d,
	   questionnaire qstnr,
	   answerSection aSection,
	   questionSection qs,
	   answer A,
	   section S,
	   question Q,
	   patient p,
	   `type` t
	WHERE
	   AQ.questionnaireId=qstnr.ID
	   AND S.questionnaireId=qstnr.ID
	   AND qs.sectionId = S.ID
	   AND Q.ID=qs.questionId
	   AND AQ.patientId=p.ID
		AND p.externalId=%s
	   AND AQ.`status` = 2
	   AND AQ.lastUpdated>%s
	   AND AQ.ID = aSection.answerQuestionnaireId
	   AND aSection.ID = A.answerSectionId
	   AND A.deleted = 0
	   AND A.answered = 1
	   AND A.questionId = Q.ID
	   AND A.typeId=t.ID
	   AND t.description=d.contentId
	   AND d.languageId=2
	   AND qstnr.purposeId IN (1,2)
	)
;
