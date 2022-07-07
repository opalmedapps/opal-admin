"""This module provides `ModelForm` for the `hospital_settings` using crispy forms."""

from typing import Any

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Layout, Submit

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
        image_html_en = """
            {% if form.logo_en.value %}
                <img class="img-fluid" src="{{ MEDIA_URL }}{{ form.logo_en.value }}">
            {% endif %}
        """
        image_html_fr = """
            {% if form.logo_fr.value %}
                <img class="img-fluid" src="{{ MEDIA_URL }}{{ form.logo_fr.value }}">
            {% endif %}
        """
        self.helper.layout = Layout(
            'name_en',
            'name_fr',
            'logo_en',
            HTML(image_html_en),
            'logo_fr',
            HTML(image_html_fr),
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
