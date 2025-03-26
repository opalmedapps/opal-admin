"""App core util functions."""
import secrets
import string


def generate_random_number(length: int) -> str:
    """Generate random number with the parameter length.

    Args:
        length: length of the number.

    Returns:
        return a string number
    """
    return ''.join(secrets.choice(string.digits) for ii in range(length))
