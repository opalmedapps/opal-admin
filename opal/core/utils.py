"""App core util functions."""
import csv
import io
import random
import secrets
import string
import uuid
from typing import Any

import qrcode
from qrcode.image import svg


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


def generate_random_registration_code(institution_code: str, length: int) -> str:
    """Generate a random alphanumeric string with a given length.

    Args:
        institution_code: intitution code for registration.
        length: length of a random alphanumeric string.

    Returns:
        return a random alphanumeric string
    """
    # getting systemRandom instance out of random class to prevent flake8 S311 vioaltion
    # and generate cryptographically secure random.
    system_random = random.SystemRandom()
    return institution_code + ''.join(
        system_random.choices(string.ascii_letters + string.digits, k=length),
    )


def qr_code(text: str) -> bytes:
    """
    Create a QR code for the given text.

    Args:
        text: text to encode in the QR code

    Returns:
        the in-memory image as bytes
    """
    code = qrcode.QRCode(
        version=1,
        border=0,
    )
    code.add_data(text)
    code.make(fit=True)

    image = code.make_image(
        image_factory=svg.SvgImage,
        back_color='white',
        fill_color='white',
    )

    stream = io.BytesIO()
    image.save(stream)

    return stream.getvalue()


def dict_to_csv(input_dict: list[dict[str, Any]]) -> bytes:
    """Convert a list of dictionaries to CSV bytes.

    The CSV data is returned in `bytes` format.

    Args:
        input_dict: list of dictionaries with string keys and values of any type

    Returns:
        `bytes` object containing the CSV data
    """
    # Collect all possible headers from the list of dictionaries
    headers = input_dict[0].keys() if input_dict else []

    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    writer.writerows(input_dict)

    csv_string = buffer.getvalue()
    # Encode the string to bytes
    return csv_string.encode('utf-8')
