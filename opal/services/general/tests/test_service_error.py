from opal.services.general.service_error import ServiceErrorHandler

service_error = ServiceErrorHandler()


# generate_error


def test_generate_error() -> None:
    """Ensure error message is in JSON format and has specific fields."""
    error_message = {'message1': 'message1', 'message2': 'message2'}
    error = service_error.generate_error(error_message)
    assert isinstance(error['status'], str) is True
    assert error['status'] == 'error'
    assert error['data'] == error_message


def test_generate_error_empty() -> None:
    """Ensure an empty JSON does not cause an error."""
    error = service_error.generate_error({})
    assert error['status'] == 'error'
    assert bool(error['data']) is False


def test_generate_error_none() -> None:
    """Ensure non-dictionary type does not cause an error."""
    error = service_error.generate_error(123)  # type: ignore[arg-type]

    assert error['data'] == 123
    assert error['status'] == 'error'
