"""Module providing validation rules for the data being sent/received to/from the patient apis."""
from typing import Any

from .api_data import RegistrationRegisterData, SecurityAnswerData


class RegisterApiValidator:
    """Patient api helper service that validates patient api request data."""

    def is_register_data_valid(  # noqa: C901 WPS210 WPS213 WPS231
        self,
        request_data: Any,
    ) -> tuple[RegistrationRegisterData, list]:
        """Check if the api Registration/<code>/register input data is valid.

        Args:
            request_data (Any): Api Registration/<code>/register input data.

        return:
            return a tuple including RegistrationRegisterData and errors list
        """
        errors: list = []

        patient_data = None
        try:
            patient_data = request_data['patient']
        except (KeyError):
            errors = []

        legacy_id = 0
        if patient_data:
            try:
                legacy_id = patient_data['legacy_id']
            except (KeyError):
                errors.append('Register data does not have the attribute patient => legacy_id')
        else:
            errors.append('Register data attribute patient is empty or does not exist')

        caregiver_data = None
        try:
            caregiver_data = request_data['caregiver']
        except (KeyError):
            errors.append('Register data does not have the attribute caregiver')

        language = ''
        email = ''
        phone = ''
        security_answers = []
        security_answer_data = None
        if caregiver_data:
            try:
                language = caregiver_data['language']
            except (KeyError):
                errors.append('Caregiver data does not have the attribute language')

            try:
                email = caregiver_data['email']
            except (KeyError):
                errors.append('Caregiver data does not have the attribute email')

            try:
                phone = caregiver_data['phone_number']
            except (KeyError):
                errors.append('Caregiver data does not have the attribute phone_number')

            try:
                security_answer_data = caregiver_data['security_answers']
            except (KeyError):
                errors.append('Caregiver data does not have the attribute security_answers')

        if security_answer_data:
            for answer_data in security_answer_data:
                try:
                    question = answer_data['question']
                except (KeyError):
                    errors.append('One of security answer data missed the attribute question')
                    break
                try:
                    answer = answer_data['answer']
                except (KeyError):
                    errors.append('One of security answer data missed the attribute answer')
                    break
                security_answers.append(SecurityAnswerData(question=question, answer=answer))

        return (
            RegistrationRegisterData(
                legacy_id=int(legacy_id),
                language=str(language),
                email=str(email),
                phone_number=str(phone),
                security_answers=security_answers,
            ),
            errors,
        )
