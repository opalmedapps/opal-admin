"""App core util functions."""
import secrets
import string
import uuid


def generate_random_number(length: int) -> str:
    """Generate random number with the parameter length.

    Args:
        length: length of the number.

    Returns:
        return a string number
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_random_uuid(length: int) -> str:
    """Generate a random uuid hexadecimal string with a given length.

    Args:
        length: length of a random uuid hexadecimal string.

    Returns:
        return a random uuid hexadecimal string
    """
    return uuid.uuid4().hex[:length]
