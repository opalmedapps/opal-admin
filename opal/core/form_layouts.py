"""Module providing custom crispy layout objects."""

from django.utils.translation import gettext_lazy as _

from crispy_forms.layout import HTML, Field


class ImageFieldWithPreview(Field):
    """Image input field with a preview block."""

    template = 'forms/image_input_preview.html'


class CancelButton(HTML):
    """Reusable cancel button."""

    def __init__(self, url: str) -> None:
        """`Cancel` button with custom style.

        Args:
            url (str): link to a page that the user will be redirected to
        """
        cancel_text = _('Cancel')
        html = f'<a class="btn btn-secondary mr-2" href="{url}">{cancel_text}</a>'

        super().__init__(html)
