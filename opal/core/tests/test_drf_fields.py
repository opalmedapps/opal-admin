import base64
from pathlib import Path

from django.core.files import File
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


def test_to_representation_file() -> None:
    """Test with a regular file path."""
    with Path('opal/tests').joinpath('test.pdf').open('rb') as terms_file:
        terms_file.write(b'test')
        file = File(terms_file)
        file_model = TestBase64Model(field_file=file)

    field_file = FieldFile(file_model, file_model.file_field, 'test')
    assert Base64FileField().to_representation(field_file) == base64.b64encode(b'test')
