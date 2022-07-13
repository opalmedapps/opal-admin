"""Module providing custom crispy fields."""

from crispy_forms.layout import Field


class ImageFieldWithPreview(Field):
    """Image input field with a preview block."""

    template = 'image_input_preview.html'
