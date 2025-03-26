from ..utils import generate_random_registration_code, generate_random_uuid


def test_random_uuid_length() -> None:
    """Test the length of random uuid."""
    length = 30
    uuid = generate_random_uuid(length)
    assert len(uuid) == length


def test_random_uuid_is_string() -> None:
    """Ensure the random uuid is string."""
    uuid = generate_random_uuid(30)
    assert isinstance(uuid, str)


def test_random_uuid_is_unique() -> None:
    """Ensure the random uuid is unique."""
    uuid1 = generate_random_uuid(30)
    uuid2 = generate_random_uuid(30)
    assert uuid1 != uuid2


def test_random_registration_code_length() -> None:
    """Test the length of random registration code."""
    length = 10
    code = generate_random_registration_code(length)
    assert len(code) == length


def test_random_registration_code_is_string() -> None:
    """Ensure the random registration code is string."""
    code = generate_random_registration_code(10)
    assert isinstance(code, str)


def test_random_registration_code_is_unique() -> None:
    """Ensure the random registration code is unique."""
    code1 = generate_random_uuid(10)
    code2 = generate_random_uuid(10)
    assert code1 != code2


def test_code_only_contains_letters_and_numbers() -> None:
    """Ensure the random registration code only contains letters and numbers."""
    code = generate_random_registration_code(10)
    assert code.isalnum()
