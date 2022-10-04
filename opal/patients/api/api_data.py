"""Module providing custom input data structures (a.k.a., named tuples) for the patient apis."""
from typing import List, NamedTuple


class SecurityAnswerData(NamedTuple):
    """Typed `NamedTuple` that describes SeurityAnswer fields (a.k.a., SecurityAnswer data structure).

    These fields are the input from the Registration/<code>/register.

    Attributes:
        question (str): one of the SecurityAnswer field
        answer (str): one of the SecurityAnswer  field
    """

    question: str
    answer: str


class RegistrationRegisterData(NamedTuple):
    """Typed `NamedTuple` that describes api input fields.

    These fields are the input from the Registration/<code>/register.

    Attributes:
        legacy_id (str): the patient legacy_id
        language (str): the language of the user
        phone (str): phone number of the user
        email (str): email address of the user
        security_answers (SecurityAnswerData): list of SercurityAnswers
    """

    legacy_id: int
    language: str
    phone_number: str
    email: str
    security_answers: List[SecurityAnswerData]
