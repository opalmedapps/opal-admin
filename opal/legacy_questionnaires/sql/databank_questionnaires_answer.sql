SELECT
   A.*,
   answerSlider.VALUE AS answer_value
FROM
   tempAnswerDetails A,
   answerSlider
WHERE
   answerSlider.answerId = A.question_answer_id
   AND A.question_type_id = 2

UNION

SELECT
   A.*,
   answerDate.VALUE AS answer_value
FROM
   tempAnswerDetails A,
   answerDate
WHERE
   answerDate.answerId = A.question_answer_id
   AND A.question_type_id = 7

UNION

SELECT
   A.*,
   answerTime.VALUE AS answer_value
FROM
   tempAnswerDetails A,
   answerTime
WHERE
   answerTime.answerId = A.question_answer_id
   AND A.question_type_id = 6

UNION

SELECT
   A.*,
   getDisplayName(rbOpt.description, 2) AS answer_value
FROM
   tempAnswerDetails A,
   answerRadioButton aRB,
   radioButtonOption rbOpt
WHERE
   aRB.answerId = A.question_answer_id
   AND rbOpt.ID = aRB.`value`
   AND A.question_type_id = 4

UNION

SELECT
   A.*,
   getDisplayName(cOpt.description, 2) AS answer_value
FROM
   tempAnswerDetails A,
   answerCheckbox aC,
   checkboxOption cOpt
WHERE
   aC.answerId = A.question_answer_id
   AND cOpt.ID = aC.`value`
   AND A.question_type_id = 1

UNION

SELECT
   A.*,
   getDisplayName(lOpt.description, 2) AS answer_value
FROM
   tempAnswerDetails A,
   answerLabel aL,
   labelOption lOpt
WHERE
   aL.answerId = A.question_answer_id
   AND lOpt.ID = aL.`value`
   AND A.question_type_id = 5
;
