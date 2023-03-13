import base64
from pathlib import Path

from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from ..drf_fields import Base64FileField


class TestBase64Model(models.Model):
    """Class wrapper for Base64FileField tests."""

    file_field = models.FileField()

    class Meta:
        verbose_name = _('TestBase64')
        verbose_name_plural = _('TestsBase64')

    def __str__(self) -> str:
        """
        Return the string representation of the location.

        Returns:
            test message
        """
        return 'test'


def test_to_representation_file(test_path: Path) -> None:
    """Test with a regular file path."""
    test_path.joinpath('media').mkdir()
    test_file = test_path.joinpath('media').joinpath('test.pdf')
    with test_file.open('w') as fd:
        fd.write('test')

    test_model = TestBase64Model()
    test_model.file_field.path = test_file
    field_file = FieldFile(test_model, test_model.file_field, 'test.pdf')

    assert Base64FileField().to_representation(field_file) == base64.b64encode(b'test')
