"""This module provides filters for `patients` app."""
from typing import Any, Dict

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import gettext

import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Layout

from opal.hospital_settings.models import Site

from ..core.forms.layouts import InlineReset, InlineSubmit
from .models import User


class UserFilterForm(forms.Form):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the filter and set the form layout for the search area of the "Manage Caregiver Access" page.

        The form contains fields for the medical card type (MRN or RAMQ), sites' codes, and medical number.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        # self.helper.form_class = 'form-inline row row-cols-lg-auto g-3 align-items-baseline'
        self.helper.attrs = {'novalidate': ''}
        self.helper.form_method = 'GET'
        self.helper.disable_csrf = True

        self.helper.layout = Layout(
            Div(
                Column('email'),
                Column('phone_number'),
                Column(InlineSubmit(
                    name='',
                    label=gettext('Search'),
                )),
                Column(InlineReset(
                    label=gettext('Reset'),
                )),
                css_class='form-inline row row-cols-lg-auto g-3 align-items-baseline',
            ),
        )

    def clean(self) -> dict[str, Any]:
        cleaned_data = self.cleaned_data

        email_address = cleaned_data.get('email')
        phone_number = cleaned_data.get('phone_number')

        if not email_address and not phone_number:
            self.add_error(NON_FIELD_ERRORS, gettext('Either email address or phone number is required'))

        return cleaned_data


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        form = UserFilterForm
        fields = ['email', 'phone_number']
