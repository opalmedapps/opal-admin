import base64
from pathlib import Path

from django.db.models.fields.files import FieldFile

from ..drf_fields import Base64FileField


# copied from: https://github.com/Hipo/drf-extra-fields/blob/master/tests/test_fields.py
class _FieldFile:
    """A fake FieldFile class in purpose of unit testing."""

    def __init__(self, path: str):
        """
        Set the fake FieldFile class.

        Args:
            path: tmp path for testing in string format
        """
        self.path = path


class _DownloadableBase64File:
    """The class to instantiated the fake FieldFile class."""

    def __init__(self, file_path: Path):
        """
        Set the DownloadableBase64File class.

        Args:
            file_path: the path Oject for FieldFile class.
        """
        self.file = _FieldFile(path=str(file_path))


def test_base64filefield_to_representation(tmp_path: Path) -> None:
    """Ensure the `Base64FileField` returns the base64 encoded content of the file."""
    test_file = tmp_path.joinpath('test.txt')
    with test_file.open('wb') as fd:
        fd.write(b'test')

    field_file: FieldFile = _DownloadableBase64File(test_file).file  # type: ignore[assignment]
    assert Base64FileField().to_representation(field_file) == base64.b64encode(b'test').decode('utf-8')
