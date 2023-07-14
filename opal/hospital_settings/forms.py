"""This module provides `ModelForm` for the `hospital_settings` using crispy forms."""

from typing import Any

from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Submit

from opal.core.forms.layouts import CancelButton, FileField, FormActions

from .models import Institution


class InstitutionForm(forms.ModelForm[Institution]):
    """Form for creating/updating an `Institution` object."""

    class Meta:
        model = Institution
        fields = (
            'name_en',
            'name_fr',
            'code',
            'support_email',
            'adulthood_age',
            'non_interpretable_lab_result_delay',
            'interpretable_lab_result_delay',
            'logo_en',
            'logo_fr',
            'terms_of_use_en',
            'terms_of_use_fr',
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            'name_en',
            'name_fr',
            'code',
            'support_email',
            FileField('logo_en'),
            FileField('logo_fr'),
            FileField('terms_of_use_en'),
            FileField('terms_of_use_fr'),
            Column('adulthood_age', css_class='col-3'),
            Column('non_interpretable_lab_result_delay', css_class='col-3'),
            Column('interpretable_lab_result_delay', css_class='col-3'),
            FormActions(
                CancelButton(reverse('hospital-settings:institution-list')),
                Submit('submit', _('Save')),
            ),
        )
