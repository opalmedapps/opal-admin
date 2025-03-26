from ..orms_validation import ORMSValidator

orms_validator = ORMSValidator()


def test_patient_response_no_status() -> None:
    """An error message is returned when the patient response has no status."""
    response = {
        'error': 'Message',
    }

    valid, errors = orms_validator.is_patient_response_valid(response)
    assert not valid
    assert errors == ['Patient response data does not have the attribute "status"']


def test_patient_response_success() -> None:
    """The response is considered valid if the status is 'Success'."""
    response = {
        'status': 'Success',
    }

    valid, errors = orms_validator.is_patient_response_valid(response)
    assert valid
    assert not errors


def test_patient_response_error() -> None:
    """The response is considered invalid if the status is 'Error'."""
    response = {
        'status': 'Error',
    }

    valid, errors = orms_validator.is_patient_response_valid(response)
    assert not valid
    assert errors == ['Error response from ORMS']


def test_patient_response_not_found() -> None:
    """A special error message is returned when the patient is not found."""
    response = {
        'status': 'Error',
        'error': 'Patient not found',
    }

    valid, errors = orms_validator.is_patient_response_valid(response)
    assert not valid
    assert errors == [
        'Error response from ORMS',
        'Skipping patient initialization in ORMS because the patient was not found there',
    ]


def test_patient_response_malformed() -> None:
    """An error message is returned when the patient response contains unexpected values."""
    response = {
        'status': 'Other',
    }

    valid, errors = orms_validator.is_patient_response_valid(response)
    assert not valid
    assert errors == ['Patient response data is in an unexpected format']
