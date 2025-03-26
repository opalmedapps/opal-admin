"""This module provides `ModelForm` for the `hospital_settings` using crispy forms."""

from typing import Any

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Submit

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
        super().__init__(*args, **kwargs)
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
            Submit('submit', 'Submit', css_class='btn btn-primary'),
        )
