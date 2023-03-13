import base64
from pathlib import Path

from django.db.models.fields.files import FieldFile

from ..drf_fields import Base64FileField


# copied from: https://github.com/Hipo/drf-extra-fields/blob/master/tests/test_fields.py
class _FieldFile:
    def __init__(self, path: str):
        self.path = path


class _DownloadableBase64File:
    def __init__(self, file_path: Path):
        self.file = _FieldFile(path=str(file_path))


def test_base64filefield_to_representation(tmp_path: Path) -> None:
    """The `Base64FileField` returns the base64 encoded content of the file."""
    test_file = tmp_path.joinpath('test.txt')
    with test_file.open('wb') as fd:
        fd.write(b'test')

    field_file: FieldFile = _DownloadableBase64File(test_file).file  # type: ignore[assignment]
    assert Base64FileField().to_representation(field_file) == base64.b64encode(b'test')
