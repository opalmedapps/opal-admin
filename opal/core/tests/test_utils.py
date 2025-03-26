import io
import zipfile

from .. import utils

# Sample file contents
file_contents = {
    'file1.txt': b'Hello, this is file 1.',
    'file2.txt': b'This is the content of file 2.',
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


def test_create_zip_from_bytesio_empty_list() -> None:
    """Ensure create_zip_from_bytesio does not fail when it receives an empty list."""
    file_list: list[tuple[str, io.BytesIO]] = []

    # Invoke the function with the empty list
    zip_bytes_io = utils.create_zip_from_bytesio(file_list)

    # Ensure the returned object is a BytesIO instance
    assert isinstance(zip_bytes_io, io.BytesIO), 'The returned object should be a BytesIO even the file list is empty.'

    # Ensure the zip buffer is not None
    assert zip_bytes_io is not None, 'The ZIP buffer should not be None.'

    # Ensure the zip buffer is not empty (an empty zip file has some bytes)
    assert zip_bytes_io.getbuffer().nbytes > 0, 'The zip buffer should contain data even for an empty zip file.'

    # Open the zip file from the BytesIO object
    with zipfile.ZipFile(zip_bytes_io, 'r') as zip_file:
        # Get the list of files in the zip archive
        zip_contents = zip_file.namelist()

        # Assert that the zip archive is empty
        assert not zip_contents, 'The zip archive should be empty when the file list is empty.'


def test_create_zip_from_bytesio_success() -> None:
    """Ensure a ZIP file can be successfully created as an in-memory BytesIO object."""
    # Create the list of (filename, BytesIO object) pairs
    file_list = [
        (filename, io.BytesIO(content)) for filename, content in file_contents.items()
    ]

    zip_bytes_io = utils.create_zip_from_bytesio(file_list)

    assert isinstance(zip_bytes_io, io.BytesIO), 'The returned object should be a BytesIO instance.'
    assert zip_bytes_io.getbuffer().nbytes != 0, 'The ZIP buffer should not be empty.'


def test_create_zip_from_bytesio_contains_all_files() -> None:
    """Ensure that all expected files are in the zip archive."""
    # Create the list of (filename, BytesIO object) pairs
    file_list = [
        (filename, io.BytesIO(content)) for filename, content in file_contents.items()
    ]

    zip_bytes_io = utils.create_zip_from_bytesio(file_list)

    # Open the zip file from the BytesIO object
    with zipfile.ZipFile(zip_bytes_io, 'r') as zip_file:
        # Get the list of files in the zip archive
        zip_contents = zip_file.namelist()

        expected_files = list(file_contents.keys())

        assert set(zip_contents) == set(expected_files), (
            f'ZIP archive contents {zip_contents} do not match expected {expected_files}.'
        )


def test_create_zip_from_bytesio_contains_files_contents() -> None:
    """Ensure that in the ZIP archive the contents of each file are the same as the original ones."""
    # Create the list of (filename, BytesIO object) pairs
    file_list = [
        (filename, io.BytesIO(content)) for filename, content in file_contents.items()
    ]

    zip_bytes_io = utils.create_zip_from_bytesio(file_list)

    # Open the zip file from the BytesIO object
    with zipfile.ZipFile(zip_bytes_io, 'r') as zip_file:
        expected_files = list(file_contents.keys())

        # Verify the contents of each file
        for filename in expected_files:
            with zip_file.open(filename) as zipped_file:
                content = zipped_file.read()
                assert content == file_contents[filename], f'Contents of {filename} do not match.'
