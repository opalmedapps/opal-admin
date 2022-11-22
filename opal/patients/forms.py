"""This module provides `ModelForm` for the `patients` using crispy forms."""

from typing import Any

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from .models import Relationship


class RelationshipPendingAccessForm(forms.ModelForm):
    """Form for updating an `Pending Relationship Access` object."""

    start_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Relationship
        fields = (
            'start_date',
            'end_date',
            'status',
            'reason',
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Set the layout.

        Args:
            args: varied amount of non-keyworded arguments
            kwargs: varied amount of keyworded arguments
        """
        kwargs['initial']['start_date'] = str(kwargs['instance'].start_date)
        kwargs['initial']['end_date'] = str(kwargs['instance'].end_date)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'start_date',
            'end_date',
            'status',
            'reason',
        )
