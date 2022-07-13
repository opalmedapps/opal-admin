"""This module provides `ModelForm` for the `hospital_settings` using crispy forms."""

from typing import Any

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Layout, Submit

from opal.core.fields import ImageFieldWithPreview

from .models import Institution


class InstitutionForm(forms.ModelForm):
    """Form for creating/updating an `Institution` object."""

    class Meta:
        model = Institution
        fields = ('name_en', 'name_fr', 'logo_en', 'logo_fr', 'code')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Change the queryset using `__init__`.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super(InstitutionForm, self).__init__(*args, **kwargs)  # noqa: WPS608
        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            'name_en',
            'name_fr',
            ImageFieldWithPreview('logo_en'),
            ImageFieldWithPreview('logo_fr'),
            'code',
            FormActions(
                Submit('submit', _('Save'), css_class='btn btn-primary'),
                Button(
                    'cancel',
                    _('Cancel'),
                    css_class='btn btn-secondary mr-2',
                    onclick="window.location.href = '{0}';".format(
                        reverse_lazy('hospital-settings:institution-list'),
                    ),
                ),
            ),
        )
