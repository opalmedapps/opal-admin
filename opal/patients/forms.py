"""This module provides forms for Patients."""
from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit

from opal.core import validators

from . import constants
from .models import Site


class SelectSiteForm(forms.Form):
    """This `SelectSiteForm` provides a group of buttons to choose hospital site."""

    sites = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        widget=forms.RadioSelect,
        label=_('At which hospital is the patient?'),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for site buttons.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('sites', css_class='form-group col-md-12 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Next')),
            ),
        )


class SearchForm(forms.Form):
    """This `SearchForm` provides the layout for MRN or RAMQ type and number."""

    medical_card = forms.ChoiceField(
        widget=forms.Select(),
        choices=constants.MEDICAL_CARDS,
        label=_('Please Select A Card Type'),
    )

    medical_number = forms.CharField(
        widget=forms.TextInput(),
        label=_('Please Input The Card Number'),
        validators=[validators.validate_ramq],
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for card type select box and card number input box.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('medical_card', css_class='form-group col-md-3 mb-0'),
                Column('medical_number', css_class='form-group col-md-3 mb-0'),
                css_class='form-row',
            ),
            ButtonHolder(
                Submit('wizard_goto_step', _('Generate QR Code')),
            ),
        )
