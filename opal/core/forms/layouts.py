# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing custom crispy layout objects."""

from typing import Any

from django.utils.translation import gettext_lazy as _

from crispy_forms.bootstrap import FormActions as CrispyFormActions
from crispy_forms.layout import HTML, Field, Layout, Submit
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
    default_css_class = 'btn d-table'

    def __init__(
        self,
        name: str,
        label: str | None = None,
        extra_css: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the inline submit button.

        The submit button is an input of type submit

        Args:
            name: the name of the submit button, empty string if you don't need to identify it
            label: label of the submit button, defaults to `Submit` otherwise
            extra_css: optional additional CSS classes
            kwargs: additional keyword arguments that are added to the submit button
        """
        the_label = label or self.default_label

        submit = Submit(name, the_label, **kwargs)

        if extra_css:
            submit.field_classes = f'{self.default_css_class} {extra_css}'
        else:
            submit.field_classes = f'{self.default_css_class} btn-selected'

        fields = (
            HTML(f'<label class="form-label invisible d-sm-none d-md-inline-block">{the_label}</label>'),
            submit,
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
    default_css_class = 'btn d-table'

    def __init__(
        self,
        label: str | None = None,
        extra_css: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the inline reset button.

        The reset button is a link styled as a button.

        Args:
            label: label of the reset button, default to `Reset` otherwise
            extra_css: optional additional CSS classes
            kwargs: additional keyword arguments that are added to the reset button
        """
        the_label = label or self.default_label
        flat_attrs = flatatt(kwargs)

        url = '{{request.path}}'

        css_class = f'{self.default_css_class} {extra_css}' if extra_css else f'{self.default_css_class} btn-unselected'

        fields = (
            HTML(f'<label class="form-label invisible d-sm-none d-md-inline-block">{the_label}</label>'),
            HTML(
                f'<a class="{css_class}" href="{url}" {flat_attrs}>{the_label}</a>',
            ),
        )
        super().__init__(*fields)


class FormActions(CrispyFormActions):
    """Default form actions."""

    default_css_class = 'd-flex justify-content-end gap-2'

    def __init__(
        self,
        *fields: Any,
        css_id: str | None = None,
        css_class: str | None = None,
        template: str | None = None,
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


class EnterSuppressedLayout(Layout):
    """Default layout to suppress submission on pressing enter-key."""

    def __init__(self, *fields: Any) -> None:
        """
        Override initialization of Layout component for crispyforms.

        Args:
            fields: field list passed to initialize the layout
        """
        self.fields = list(fields)
        super().__init__(
            HTML('<button type="submit" disabled style="display: none" aria-hidden="true"></button>'),
            *fields,
        )


class RadioSelect(Field):
    """
    Custom radio select widget to be used for radio button tooltip, help_text, errors.

    Triggers validation via `up-validate` on selection to let the form react to the selection.
    Supports option tooltip on the radio select label.
    """

    template = 'forms/radioselect.html'


# potential improvement: inherit from Container or LayoutObject to include the content
# and provide a method to add content at the right place
class TabRadioSelect(Field):
    """
    Custom radio select widget to be used for visualizing choices as Bootstrap tabs.

    Triggers validation via `up-validate` on selection to let the form react to the selection.
    For example, the form can change the layout according to the selection.
    """

    template = 'forms/radioselect_tabs.html'
