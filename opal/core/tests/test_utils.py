from ..utils import generate_random_uuid


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
