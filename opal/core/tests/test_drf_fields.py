from typing import Any, Optional

from opal.utils.base64 import Base64Util

from ..drf_fields import Base64FileField

TXT_FILE_PATH = 'opal/tests/fixtures/test_txt.txt'
PDF_FILE_PATH = 'opal/tests/fixtures/test_PDF.pdf'


class TestBase64PDFFileField:
    """Class wrapper for Base64PDFFileField tests."""

    class_instance = Base64FileField()
    base64_util = Base64Util()

    def set_args(self, path: Optional[Any]) -> None:
        """Set the input arguments expected by Base64PDFFileField."""
        if path:
            self.path = path

    def to_represent(self) -> Optional[Any]:
        """
        Execute the call to the representation method.

        Returns:
            The result of calling Base64PDFFileField.
        """
        return self.class_instance.to_representation(self.path)

    def test_to_representation_pdf_file(self) -> None:
        """Test with a regular PDF file path."""
        self.set_args(PDF_FILE_PATH)
        base64_str = self.to_represent()

        assert base64_str
        assert self.base64_util.is_base64(base64_str)

    def test_to_representation_invalid_file(self) -> None:
        """Test with an invalid file path."""
        self.set_args('test/invalid/path')

        try:
            base64_str = self.to_represent()
        except OSError:
            assert base64_str == ''

    def test_to_representation_no_pdf_file(self) -> None:
        """Test with a non PDF file path."""
        self.set_args(TXT_FILE_PATH)

        try:
            base64_str = self.to_represent()
        except OSError:
            assert base64_str == ''
