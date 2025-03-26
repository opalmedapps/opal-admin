from typing import Any

from .. import utils


def test_random_uuid_length() -> None:
    """Test the length of random uuid."""
    length = 30
    uuid = utils.generate_random_uuid(length)
    assert len(uuid) == length


def test_random_uuid_is_string() -> None:
    """Ensure the random uuid is string."""
    uuid = utils.generate_random_uuid(30)
    assert isinstance(uuid, str)


def test_random_uuid_is_unique() -> None:
    """Ensure the random uuid is unique."""
    uuid1 = utils.generate_random_uuid(30)
    uuid2 = utils.generate_random_uuid(30)
    assert uuid1 != uuid2


def test_random_registration_code_format() -> None:
    """Ensure if random registration code is alpha-numeric string and equal to the given length."""
    length = 10
    test_institution_code = 'XX'
    code = utils.generate_random_registration_code(test_institution_code, length)
    assert len(code) == length + len(test_institution_code)
    assert isinstance(code, str)
    assert code.isalnum()


def test_random_registration_code_is_unique() -> None:
    """Ensure the random registration code is unique."""
    code1 = utils.generate_random_registration_code('XX', 10)
    code2 = utils.generate_random_registration_code('XX', 10)
    assert code1 != code2


def test_qr_code() -> None:
    """Ensure a QR code can be built as an in-memory SVG image."""
    code = utils.qr_code('https://opalmedapps.ca')

    assert code.startswith(b'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<svg xmlns:svg="http://www.w3.org/2000/svg"')


def test_dict_to_csv_bytesio_success() -> None:
    """Ensure dict_to_csv_bytesio successfully converts a flat dictionary to a CSV file."""
    input_dict: dict[str | int, Any] = {'name': 'Alice', 'age': '30', 'city': 'New York'}
    expected_csv = 'name,age,city\r\nAlice,30,New York\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_empty() -> None:
    """Ensure dict_to_csv_bytesio successfully creates a CSV file for an empty dictionary."""
    input_dict: dict[str | int, Any] = {}
    expected_csv = '\r\n\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_special_chars() -> None:
    """Ensure dict_to_csv_bytesio successfully converts dict with values containing special characters."""
    input_dict: dict[str | int, Any] = {
        'key1': 'value1, with comma',
        'key2': 'value\nwith newline',
        'key3': 'value "with quotes"',
    }
    expected_csv = (
        'key1,key2,key3\r\n'
        + '"value1, with comma","value\nwith newline","value ""with quotes"""\r\n'
    )
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_numbers() -> None:
    """Ensure dict_to_csv_bytesio successfully converts dict with numeric values."""
    input_dict: dict[str | int, Any] = {'integer': 123, 'float': 0.5, 'none': None}
    expected_csv = 'integer,float,none\r\n123,0.5,\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_non_string_keys() -> None:
    """Ensure dict_to_csv_bytesio successfully converts dict with non-string keys."""
    input_dict: dict[str | int, Any] = {1: 'one', 2: 'two', 3: 'three'}
    expected_csv = '1,2,3\r\none,two,three\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_boolean_values() -> None:
    """Ensure dict_to_csv_bytesio successfully converts dict with boolean values."""
    input_dict: dict[str | int, Any] = {'is_active': True, 'is_admin': False}
    expected_csv = 'is_active,is_admin\r\nTrue,False\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_order_preservation() -> None:
    """Ensure dict_to_csv_bytesio preserves the order of the keys."""
    input_dict: dict[str | int, Any] = {'first': 1, 'second': 2, 'third': 3}
    expected_csv = 'first,second,third\r\n1,2,3\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_unicode_characters() -> None:
    """Ensure dict_to_csv_bytesio successfully converts dict Unicode characters."""
    input_dict: dict[str | int, Any] = {'montreal': 'Montréal', 'greeting': 'こんにちは', 'farewell': 'さようなら'}
    expected_csv = 'montreal,greeting,farewell\r\nMontréal,こんにちは,さようなら\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_large_numbers() -> None:
    """Ensure dict_to_csv_bytesio successfully converts dict with very large numbers."""
    input_dict: dict[str | int, Any] = {
        'big_int': 12345678901234567890,
        'big_float': 1.2345678901234567890,  # noqa: WPS339
    }
    expected_csv = 'big_int,big_float\r\n12345678901234567890,1.2345678901234567\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    # Adjust expected output for floating-point precision
    assert csv_content == expected_csv


def test_dict_to_csv_bytesio_none_values() -> None:
    """Ensure dict_to_csv_bytesio successfully converts dict with None values."""
    input_dict: dict[str | int, Any] = {'key1': None, 'key2': 'value2'}
    expected_csv = 'key1,key2\r\n,value2\r\n'
    csv_bytesio = utils.dict_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv
