import io
import zipfile
from typing import Any

from .. import utils

# Sample file contents
file_contents = {
    'file1.txt': b'Hello, this is file 1.',
    'file2.txt': b'This is the content of file 2.',
    'image.png': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00',
}


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


def test_create_zip_empty_list() -> None:
    """Ensure create_zip does not fail when it receives an empty list."""
    files: dict[str, bytes] = {}

    # Invoke the function with the empty list
    zip_bytes = utils.create_zip(files)

    # Ensure the returned object is a bytes instance
    assert isinstance(zip_bytes, bytes), 'The returned object should be a bytes object even the file list is empty.'

    # Ensure the zip buffer is not None or empty
    assert zip_bytes, 'The ZIP buffer should not be None or empty.'

    # Open the zip file from the bytes object
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_file:
        # Get the list of files in the zip archive
        zip_contents = zip_file.namelist()

        # Assert that the zip archive is empty
        assert not zip_contents, 'The zip archive should be empty when the file list is empty.'


def test_create_zip_success() -> None:
    """Ensure a ZIP file can be successfully created as an in-memory bytes object."""
    zip_bytes = utils.create_zip(file_contents)

    assert isinstance(zip_bytes, bytes), 'The returned object should be a bytes instance.'
    assert zip_bytes, 'The ZIP buffer should not be empty.'


def test_create_zip_contains_all_files() -> None:
    """Ensure that all expected files are in the zip archive."""
    zip_bytes = utils.create_zip(file_contents)

    # Open the zip file from the bytes object
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_file:
        # Get the list of files in the zip archive
        zip_contents = zip_file.namelist()

        expected_files = list(file_contents.keys())

        assert set(zip_contents) == set(expected_files), (
            f'ZIP archive contents {zip_contents} do not match expected {expected_files}.'
        )


def test_create_zip_contains_files_contents() -> None:
    """Ensure that in the ZIP archive the contents of each file are the same as the original ones."""
    zip_bytes = utils.create_zip(file_contents)

    # Open the zip file from the bytes object
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_file:
        expected_files = list(file_contents.keys())

        # Verify the contents of each file
        for filename in expected_files:
            with zip_file.open(filename) as zipped_file:
                content = zipped_file.read()
                assert content == file_contents[filename], f'Contents of {filename} do not match.'


def test_dict_to_csv_single_dict_success() -> None:
    """Ensure dict_to_csv successfully converts a single dictionary to a CSV file."""
    input_dict = [{'name': 'Alice', 'age': '30', 'city': 'New York'}]
    expected_csv = 'name,age,city\r\nAlice,30,New York\r\n'
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_multiple_dicts_success() -> None:
    """Ensure dict_to_csv successfully converts multiple dictionaries to a CSV file."""
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
    csv_bytes = utils.dict_to_csv(input_list)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_empty() -> None:
    """Ensure dict_to_csv successfully creates a CSV file for an empty list."""
    input_list: list[dict[str, Any]] = []
    expected_csv = '\r\n'
    csv_bytes = utils.dict_to_csv(input_list)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_mixed_value_types() -> None:
    """Ensure dict_to_csv successfully creates a CSV with various types of values."""
    input_list: list[dict[str, Any]] = [
        {'name': 'Alice', 'age': 30, 'is_active': True},
        {'name': 'Bob', 'age': None, 'is_active': False},
    ]
    expected_csv = 'name,age,is_active\r\nAlice,30,True\r\nBob,,False\r\n'
    csv_bytes = utils.dict_to_csv(input_list)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_special_chars() -> None:
    """Ensure dict_to_csv successfully converts list of dicts with values containing special characters."""
    input_dict = [{
        'key1': 'value1, with comma',
        'key2': 'value\nwith newline',
        'key3': 'value "with quotes"',
    }]
    expected_csv = (
        'key1,key2,key3\r\n'
        + '"value1, with comma","value\nwith newline","value ""with quotes"""\r\n'
    )
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_numbers() -> None:
    """Ensure dict_to_csv successfully converts a list of dictionaries with numeric values."""
    input_dict = [{'integer': 123, 'float': 0.5, 'none': None}]
    expected_csv = 'integer,float,none\r\n123,0.5,\r\n'
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_boolean_values() -> None:
    """Ensure dict_to_csv successfully converts list of dictionaries with boolean values."""
    input_dict = [{'is_active': True, 'is_admin': False}]
    expected_csv = 'is_active,is_admin\r\nTrue,False\r\n'
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_order_preservation() -> None:
    """Ensure dict_to_csv preserves the order of the keys."""
    input_dict = [{'first': 1, 'second': 2, 'third': 3}]
    expected_csv = 'first,second,third\r\n1,2,3\r\n'
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_unicode_characters() -> None:
    """Ensure dict_to_csv successfully converts Unicode characters."""
    input_dict = [{'montreal': 'Montréal', 'greeting': 'こんにちは', 'farewell': 'さようなら'}]
    expected_csv = 'montreal,greeting,farewell\r\nMontréal,こんにちは,さようなら\r\n'
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv


def test_dict_to_csv_large_numbers() -> None:
    """Ensure dict_to_csv successfully converts very large numbers."""
    input_dict = [
        {'big_int': 12345678901234567890, 'big_float': 1.2345678901234567890},  # noqa: WPS339
        {'big_int': 98765432109876543210, 'big_float': 9.8765432109876543210},  # noqa: WPS339
    ]
    expected_csv = (
        'big_int,big_float\r\n'
        + '12345678901234567890,1.2345678901234567\r\n'
        + '98765432109876543210,9.876543210987654\r\n'
    )
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    # Adjust expected output for floating-point precision
    assert csv_content == expected_csv


def test_dict_to_csv_none_values() -> None:
    """Ensure dict_to_csv successfully converts None values."""
    input_dict = [
        {'key1': None, 'key2': 'value2'},
        {'key1': 'value1', 'key2': None},
    ]
    expected_csv = 'key1,key2\r\n,value2\r\nvalue1,\r\n'
    csv_bytes = utils.dict_to_csv(input_dict)
    csv_content = csv_bytes.decode('utf-8')
    assert csv_content == expected_csv
