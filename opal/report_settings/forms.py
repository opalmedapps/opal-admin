"""This module provides `ModelForm` for the report templates' settings using crispy forms."""

from typing import Any

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Submit

from opal.report_settings.models import ReportTemplate


class ReportTemplateForm(forms.ModelForm):
    """Form for creating/updating a `ReportTemplate` object."""

    class Meta:
        model = ReportTemplate
        fields = ('logo_en', 'logo_fr', 'header_en', 'header_fr')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Change the queryset using `__init__`.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        super(ReportTemplateForm, self).__init__(*args, **kwargs)  # noqa: WPS608
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
            'logo_en',
            HTML(image_html_en),
            'logo_fr',
            HTML(image_html_fr),
            'header_en',
            'header_fr',
            Submit('submit', 'Submit', css_class='btn btn-primary'),
        )
