"""Module providing custom crispy layout objects."""
from typing import Any, Optional

from django.utils.translation import gettext_lazy as _

from crispy_forms.bootstrap import FormActions as CrispyFormActions
from crispy_forms.layout import HTML, Field, Layout
from crispy_forms.utils import flatatt


class FileField(Field):
    """File field with an extra button to look at the current value."""

    template = 'forms/filefield.html'


class CancelButton(HTML):
    """
    Reusable cancel button.

    The button is a link styled as a button via CSS classes.
    """

    def __init__(self, url: str) -> None:
        """
        Initialize the cancel button.

        The `url` argument does not have to be an actual URL, it can also be a template variable.
        For example, to link to the `success_url` of the page's view, use "{{view.success_url}}".
        To link to the same path, use "{{request.path}}".

        Args:
            url: URL to the page that the button will be link to
        """
        # evaluate the URL first in case it is a variable like "{{ view.success_url }}"
        html = f'{{% fragment as the_url %}}{url}{{% endfragment %}}{{% form_cancel href=the_url %}}'

        super().__init__(html)


class InlineSubmit(Layout):
    """
    Submit button that can be shown in an inline form.

    This inline submit supports inline forms with labels.
    This means that this inline submit also contains a label.
    The label is present in the output but visually hidden.
    """

    default_label = _('Submit')
    default_css_class = 'btn btn-secondary d-table'

    def __init__(
        self,
        name: str,
        label: Optional[str] = None,
        active_condition: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the inline submit button.

        The submit button is an input of type submit

        Args:
            name: name of the submit button
            label: label of the submit button, default to `Submit` otherwise
            active_condition: pass active condition to the html, not used if empty
            kwargs: additional keyword arguments that are added to the reset button
        """
        # link to the same page without query parameters to erase existing form values

        the_label = label if label else self.default_label
        css_class = f'{self.default_css_class} {active_condition}' if active_condition else self.default_css_class
        flat_attrs = flatatt(kwargs)

        fields = (
            HTML(f'<label class="form-label invisible d-sm-none d-md-inline-block">{the_label}</label>'),
            HTML(f'<input type="submit" name="{name}" value="{the_label}" class="{css_class}" {flat_attrs}>'),  # noqa: WPS221, E501
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

    default_label = _('Reset')
    default_css_class = 'btn btn-secondary d-table'

    def __init__(
        self,
        label: Optional[str] = None,
        active_condition: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the inline reset button.

        The reset button is a link styled as a button.

        Args:
            label: label of the reset button, default to `Reset` otherwise
            active_condition: pass active condition to the html, not used if empty
            kwargs: additional keyword arguments that are added to the reset button
        """
        the_label = label if label else self.default_label
        flat_attrs = flatatt(kwargs)

        # link to the same page without query parameters to erase existing form values
        url = '{{request.path}}'
        css_class = f'{self.default_css_class} {active_condition}' if active_condition else self.default_css_class
        fields = (
            HTML(f'<label class="form-label invisible d-sm-none d-md-inline-block">{the_label}</label>'),
            HTML(f'<a class="{css_class}" href="{url}" {flat_attrs}>{the_label}</a>'),  # noqa: WPS221
        )
        super().__init__(*fields)


class FormActions(CrispyFormActions):
    """Default form actions."""

    default_css_class = 'd-flex justify-content-end gap-2'

    def __init__(  # noqa: WPS211
        self,
        *fields: Any,
        css_id: Optional[str] = None,
        css_class: Optional[str] = None,
        template: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the right-aligned form actions.

        Args:
            fields: the fields to contain within this action container (should only be HTML or BaseInput)
            css_id: the ID to set for the div. Defaults to None.
            css_class: the extra CSS classes to add to the div.
            template: the template to use. Defaults to None.
            kwargs: additional keyword arguments that are added to the div
        """
        css_class = f'{self.default_css_class} {css_class}' if css_class else self.default_css_class

        super().__init__(
            *fields,
            css_id=css_id,
            css_class=css_class,
            template=template,
            **kwargs,
        )
