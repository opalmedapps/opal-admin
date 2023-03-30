"""Module providing custom crispy layout objects."""
from typing import Optional

from django.utils.translation import gettext_lazy as _

from crispy_forms.layout import HTML, Field, Layout, Submit


class FileField(Field):
    """File field with an extra button to look at the current value."""

    template = 'forms/filefield.html'


class CancelButton(HTML):
    """
    Reusable cancel button.

    The button is a link styled as a button via CSS classes.
    """

    def __init__(self, url: str, extra_css: Optional[str] = None) -> None:
        """
        Initialize the cancel button.

        The `url` argument does not have to be an actual URL, it can also be a template variable.
        For example, to link to the `success_url` of the page's view, use "{{view.success_url}}".
        To link to the same path, use "{{request.path}}".

        Args:
            url: URL to the page that the button will be link to
            extra_css: optional additional CSS classes to add to the cancel button
        """
        cancel_text = _('Cancel')
        css_classes = 'btn btn-secondary me-2'

        if extra_css:
            css_classes = f'{css_classes} {extra_css}'

        html = f'<a class="{css_classes}" href="{url}">{cancel_text}</a>'

        super().__init__(html)


class InlineSubmit(Layout):
    """
    Submit button that can be shown in an inline form.

    This inline submit supports inline forms with labels.
    This means that this inline submit also contains a label.
    The label is present in the output but visually hidden.
    """

    def __init__(self, name: str, label: str) -> None:
        """
        Initialize the submit button with the given label.

        Args:
            name: the name of the submit button, empty string if you don't need to identify it
            label: the label of the submit button
        """
        fields = (
            HTML(f'<label class="form-label invisible d-sm-none d-md-inline-block">{label}</label>'),
            Submit(name, label, css_class='d-table'),
        )
        super().__init__(*fields)


class InlineReset(Layout):
    """
    Reset button that can be shown in an inline form.

    This inline reset supports inline forms with labels.
    This means that this inline reset also contains a label.
    The label is present in the output but visually hidden.

    The reset button is not using an `<input type="reset">` because this only erases the form field values.
    """

    label = _('Reset')

    def __init__(self) -> None:
        """
        Initialize the inline reset button.

        The reset button is a link styled as a button.
        """
        # link to the same page without query parameters to erase existing form values
        url = '{{request.path}}'
        fields = (
            HTML(f'<label class="form-label invisible d-sm-none d-md-inline-block">{self.label}</label>'),
            HTML(f'<a class="btn btn-secondary me-2 d-table" href="{url}">{self.label}</a>'),
        )
        super().__init__(*fields)
