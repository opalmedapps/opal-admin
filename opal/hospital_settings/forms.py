"""This module provides `ModelForm` for the `hospital_settings` using crispy forms."""

from typing import Any

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

from ..core.form_layouts import CancelButton, ImageFieldWithPreview
from .models import Institution


class InstitutionForm(forms.ModelForm):
    """Form for creating/updating an `Institution` object."""

    class Meta:
        model = Institution
        fields = (
            'name_en',
            'name_fr',
            'logo_en',
            'logo_fr',
            'code',
            'support_email',
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
        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            'name_en',
            'name_fr',
            ImageFieldWithPreview('logo_en'),
            ImageFieldWithPreview('logo_fr'),
            'code',
            'support_email',
            'terms_of_use_en',
            'terms_of_use_fr',
            FormActions(
                Submit('submit', _('Save'), css_class='btn btn-primary'),
                CancelButton(reverse_lazy('hospital-settings:institution-list')),
            ),
        )
