# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Any

from django import forms
from django.test import RequestFactory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.utils import render_crispy_form

from ..forms import layouts


class SampleForm(forms.Form):
    """A sample form."""

    radio_select = forms.ChoiceField(
        choices=(
            ('1', 'test1'),
            ('2', 'test2'),
        ),
        initial='1',
        widget=forms.RadioSelect(attrs={'up-validate': ''}),
        error_messages={
            'error1': 'error_test1',
            'error2': 'error_test2',
        },
    )

    def __init__(self, *fields: Any, **kwargs: Any):
        """
        Initialize the form with a layout.

        Args:
            fields: any number of fields to be rendered
            kwargs: additional keyword arguments
        """
        super().__init__(**kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(*fields)


def test_cancelbutton_url() -> None:
    """Ensure the CancelButton contains the URL."""
    form = SampleForm(layouts.CancelButton('/foo'))

    html = render_crispy_form(form)

    assert 'href="/foo"' in html


def test_cancelbutton_url_variable() -> None:
    """Ensure the CancelButton can handle variables for the URL."""
    form = SampleForm(layouts.CancelButton('{{request.path}}'))

    request = RequestFactory().get('/foo')

    html = render_crispy_form(form, context={'request': request})

    assert 'href="/foo"' in html


def test_inlinesubmit() -> None:
    """Ensure the InlineSubmit shows a label and the submit button."""
    form = SampleForm(layouts.InlineSubmit('foo', 'bar'))

    html = render_crispy_form(form)

    assert 'bar</label>' in html
    assert '<input type="submit"' in html
    assert 'name="foo"' in html
    assert 'value="bar"' in html


def test_inlinesubmit_default_css() -> None:
    """Ensure the InlineSubmit supports adding extra CSS classes."""
    form = SampleForm(layouts.InlineSubmit(''))

    html = render_crispy_form(form)

    assert f'class="{layouts.InlineSubmit.default_css_class} btn-selected"' in html


def test_inlinesubmit_extra_css() -> None:
    """Ensure the InlineSubmit supports adding extra CSS classes."""
    form = SampleForm(layouts.InlineSubmit('', extra_css='btn-secondary'))

    html = render_crispy_form(form)

    assert f'class="{layouts.InlineSubmit.default_css_class} btn-secondary"' in html


def test_inlinesubmit_kwargs() -> None:
    """Ensure the InlineSubmit can handle additional arguments."""
    form = SampleForm(layouts.InlineSubmit('bar', 'foo', data_extra='test'))

    html = render_crispy_form(form)

    assert 'data-extra="test"' in html


def test_inlinesubmit_no_name() -> None:
    """Ensure the InlineSubmit can handle an empty name argument."""
    form = SampleForm(layouts.InlineSubmit(''))

    html = render_crispy_form(form)

    assert '<input type="submit"' in html
    assert 'name=""' in html


def test_inlinereset_url() -> None:
    """Ensure the InlineReset refers to the correct URL."""
    form = SampleForm(layouts.InlineReset())

    request = RequestFactory().get('/foo')

    html = render_crispy_form(form, context={'request': request})

    assert 'href="/foo"' in html


def test_inlinereset_default_label() -> None:
    """Ensure the InlineReset uses the default label."""
    form = SampleForm(layouts.InlineReset())

    html = render_crispy_form(form)

    assert 'Reset</label>' in html
    assert '>Reset</a>' in html


def test_inlinereset_custom_label() -> None:
    """Ensure the InlineReset shows the custom label."""
    form = SampleForm(layouts.InlineReset('other'))

    html = render_crispy_form(form)

    assert 'other</label>' in html
    assert '>other</a>' in html


def test_inlinereset_kwargs() -> None:
    """Ensure the InlineReset appends the additional arguments."""
    form = SampleForm(layouts.InlineReset(up_validate=True))

    html = render_crispy_form(form)

    assert ' up-validate>Reset' in html


def test_inlinereset_extra_css() -> None:
    """Ensure the InlineReset supports adding extra CSS classes."""
    form = SampleForm(layouts.InlineReset(extra_css='btn-primary'))

    html = render_crispy_form(form)

    assert f'class="{layouts.InlineReset.default_css_class} btn-primary"' in html


def test_formactions() -> None:
    """Ensure the formactions contains a div and the fields."""
    form = SampleForm(layouts.FormActions(Submit('foo', 'bar')))

    html = render_crispy_form(form)
    # make HTML one line for easier assertion
    html = ' '.join(line.strip() for line in html.split('\n'))

    assert '<div  class="mb-3 d-flex justify-content-end gap-2 "' in html
    assert '<input type="submit"' in html


def test_formactions_extra_css_class() -> None:
    """Ensure the formactions appends additional CSS classes."""
    form = SampleForm(layouts.FormActions(css_class='extra'))

    html = render_crispy_form(form)
    # make HTML one line for easier assertion
    html = ' '.join(line.strip() for line in html.split('\n'))

    assert '<div  class="mb-3 d-flex justify-content-end gap-2 extra "' in html


def test_radioselect_hidden() -> None:
    """Test radioselect hidden."""
    form = SampleForm(layouts.RadioSelect('radio_select'))
    form.fields['radio_select'].widget = forms.HiddenInput()
    html = render_crispy_form(form)

    assert '<input type="hidden"' in html


def test_radioselect_errors() -> None:
    """Test radioselect error message."""
    form = SampleForm(layouts.RadioSelect('radio_select'))
    form.fields['radio_select'].error_messages = {'required': 'This is required.'}
    assert not form.is_valid()
