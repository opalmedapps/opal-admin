import copy

from ..api.api_data import RegistrationRegisterData, SecurityAnswerData
from ..api.data_validators import RegisterApiValidator


class TestRegisterApiValidator:
    """Test RegisterApiValidator success and failure."""

    validator = RegisterApiValidator()
    valid_input_data: dict = {
        'patient': {
            'legacy_id': 1,
        },
        'caregiver': {
            'language': 'fr',
            'phone_number': '+15141112222',
            'email': 'aaa@aaa.com',
            'security_answers': [
                {
                    'question': 'correct?',
                    'answer': 'yes',
                },
                {
                    'question': 'correct?',
                    'answer': 'maybe',
                },
            ],
        },
    }

    def test_is_register_data_valid_success(self) -> None:
        """Ensure input register data valid success."""
        register_data, errors = self.validator.is_register_data_valid(self.valid_input_data)
        assert register_data == RegistrationRegisterData(
            legacy_id=1,
            language='fr',
            email='aaa@aaa.com',
            phone_number='+15141112222',
            security_answers=[
                SecurityAnswerData(
                    question='correct?',
                    answer='yes',
                ),
                SecurityAnswerData(
                    question='correct?',
                    answer='maybe',
                ),
            ],
        )
        assert not errors

    def test_is_register_data_valid_missed_patient(self) -> None:
        """Ensure input data missed attribute patient and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data.pop('patient')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.legacy_id
        assert errors == ['Register data attribute patient is empty or does not exist']

    def test_is_register_data_valid_patient_empty(self) -> None:
        """Ensure input data attribute patient is empty and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['patient'].pop('legacy_id')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.legacy_id
        assert errors == ['Register data attribute patient is empty or does not exist']

    def test_is_register_data_valid_missed_legacy_id(self) -> None:
        """Ensure input data missed attribute legacy_id and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['patient'].pop('legacy_id')
        input_data['patient']['legacy'] = 1
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.legacy_id
        assert errors == ['Register data does not have the attribute patient => legacy_id']

    def test_is_register_data_valid_missed_caregiver(self) -> None:
        """Ensure input data missed attribute caregiver and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data.pop('caregiver')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.language
        assert errors == ['Register data does not have the attribute caregiver']

    def test_is_register_data_valid_missed_language(self) -> None:
        """Ensure input data attribute caregiver missed attribute language and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['caregiver'].pop('language')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.language
        assert errors == ['Caregiver data does not have the attribute language']

    def test_is_register_data_valid_missed_email(self) -> None:
        """Ensure input data attribute caregiver missed attribute email and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['caregiver'].pop('email')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.email
        assert errors == ['Caregiver data does not have the attribute email']

    def test_is_register_data_valid_phone_number(self) -> None:
        """Ensure input data attribute caregiver missed attribute phone_number and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['caregiver'].pop('phone_number')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.phone_number
        assert errors == ['Caregiver data does not have the attribute phone_number']

    def test_is_register_data_valid_security_answers(self) -> None:
        """Ensure input data attribute caregiver missed attribute security_answers and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['caregiver'].pop('security_answers')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.security_answers
        assert errors == ['Caregiver data does not have the attribute security_answers']

    def test_is_register_data_valid_missed_question(self) -> None:
        """Ensure input data attribute caregiver missed attribute security_answers and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['caregiver']['security_answers'][0].pop('question')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.security_answers
        assert errors == ['One of security answer data missed the attribute question']

    def test_is_register_data_valid_missed_answer(self) -> None:
        """Ensure input data attribute caregiver missed attribute security_answers and return error message."""
        input_data = copy.deepcopy(self.valid_input_data)
        input_data['caregiver']['security_answers'][0].pop('answer')
        register_data, errors = self.validator.is_register_data_valid(input_data)
        assert not register_data.security_answers
        assert errors == ['One of security answer data missed the attribute answer']
