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


def test_dicts_to_csv_bytesio_single_dict_success() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts a single dictionary to a CSV file."""
    input_dict = [{'name': 'Alice', 'age': '30', 'city': 'New York'}]
    expected_csv = 'name,age,city\r\nAlice,30,New York\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_multiple_dicts_success() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts multiple dictionaries to a CSV file."""
    input_list = [
        {'name': 'Alice', 'age': 30, 'city': 'New York'},
        {'name': 'Bob', 'age': 25, 'city': 'Los Angeles'},
        {'name': 'Charlie', 'age': 35, 'city': 'Chicago'},
    ]
    expected_csv = (
        'name,age,city\r\n'
        + 'Alice,30,New York\r\n'
        + 'Bob,25,Los Angeles\r\n'
        + 'Charlie,35,Chicago\r\n'
    )
    csv_bytesio = utils.dicts_to_csv_bytesio(input_list)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_empty() -> None:
    """Ensure dicts_to_csv_bytesio successfully creates a CSV file for an empty list."""
    input_list: list[dict[str, Any]] = []
    expected_csv = '\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_list)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_mixed_value_types() -> None:
    """Ensure dicts_to_csv_bytesio successfully creates a CSV with various types of values."""
    input_list: list[dict[str, Any]] = [
        {'name': 'Alice', 'age': 30, 'is_active': True},
        {'name': 'Bob', 'age': None, 'is_active': False},
    ]
    expected_csv = 'name,age,is_active\r\nAlice,30,True\r\nBob,,False\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_list)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_special_chars() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts list of dicts with values containing special characters."""
    input_dict = [{
        'key1': 'value1, with comma',
        'key2': 'value\nwith newline',
        'key3': 'value "with quotes"',
    }]
    expected_csv = (
        'key1,key2,key3\r\n'
        + '"value1, with comma","value\nwith newline","value ""with quotes"""\r\n'
    )
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_numbers() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts a list of dictionaries with numeric values."""
    input_dict = [{'integer': 123, 'float': 0.5, 'none': None}]
    expected_csv = 'integer,float,none\r\n123,0.5,\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_boolean_values() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts list of dictionaries with boolean values."""
    input_dict = [{'is_active': True, 'is_admin': False}]
    expected_csv = 'is_active,is_admin\r\nTrue,False\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_order_preservation() -> None:
    """Ensure dicts_to_csv_bytesio preserves the order of the keys."""
    input_dict = [{'first': 1, 'second': 2, 'third': 3}]
    expected_csv = 'first,second,third\r\n1,2,3\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_unicode_characters() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts Unicode characters."""
    input_dict = [{'montreal': 'Montréal', 'greeting': 'こんにちは', 'farewell': 'さようなら'}]
    expected_csv = 'montreal,greeting,farewell\r\nMontréal,こんにちは,さようなら\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_large_numbers() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts very large numbers."""
    input_dict = [
        {'big_int': 12345678901234567890, 'big_float': 1.2345678901234567890},  # noqa: WPS339
        {'big_int': 98765432109876543210, 'big_float': 9.8765432109876543210},  # noqa: WPS339
    ]
    expected_csv = (
        'big_int,big_float\r\n'
        + '12345678901234567890,1.2345678901234567\r\n'
        + '98765432109876543210,9.876543210987654\r\n'
    )
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    # Adjust expected output for floating-point precision
    assert csv_content == expected_csv


def test_dicts_to_csv_bytesio_none_values() -> None:
    """Ensure dicts_to_csv_bytesio successfully converts None values."""
    input_dict = [
        {'key1': None, 'key2': 'value2'},
        {'key1': 'value1', 'key2': None},
    ]
    expected_csv = 'key1,key2\r\n,value2\r\nvalue1,\r\n'
    csv_bytesio = utils.dicts_to_csv_bytesio(input_dict)
    csv_content = csv_bytesio.getvalue().decode('utf-8')
    assert csv_content == expected_csv
