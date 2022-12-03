"""This module provides forms for `patients` app."""
from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit

from . import constants
from .models import Site


class ManageCaregiverAccessForm(forms.Form):
    """This `ManageCaregiverAccessForm` provides the layout for the corresponding `Manage Caregiver Access` page.

    The form contains fields for the medical card type (MRN or RAMQ), sites' codes, and medical number.
    """

    medical_card_type = forms.ChoiceField(
        widget=forms.Select(),
        choices=constants.MEDICAL_CARDS,
        label=_('Card Type'),
    )

    sites = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        widget=forms.Select,
        label=_('Site code'),
    )

    medical_number = forms.CharField(
        widget=forms.TextInput(),
        label=_('Card Number'),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the layout for the search area of the manage caregiver access page.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Row(
                Column('medical_card_type', css_class='form-group col-md-3 mb-0'),
                Column('sites', css_class='form-group col-md-3 mb-0'),
                Column('medical_number', css_class='form-group col-md-3 mb-0'),
                Submit('search', _('Search'), css_class='form-group col-md-3 mb-4 mt-4 btn btn-primary'),
                css_class='form-row',
            ),
        )
