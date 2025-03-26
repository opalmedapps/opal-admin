"""Reusable form widgets."""
from typing import Any, Optional, Union

from django import forms


class AvailableRadioSelect(forms.widgets.RadioSelect):
    """
    Subclass of Django's select widget that allows disabling options that should be unavailable.

    Use this in combination with a choice field.
    The available choices need to be provided as integers.
    I.e., for a `ModelChoiceField` it is the `pk` of each instance.

    Taken inspiration from:
        * https://stackoverflow.com/questions/673199/disabled-option-for-choicefield-django/50109362#50109362
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the '_available_choices' and '_option_descriptions'.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        self._available_choices: list[int] = []
        self._option_descriptions: dict[int, str] = {}
        super().__init__(*args, **kwargs)

    @property
    def available_choices(self) -> list[int]:
        """
        Return the available choices.

        Returns:
            the available choices
        """
        return self._available_choices

    @available_choices.setter
    def available_choices(self, other: list[int]) -> None:
        """
        Set the available choices out of all choices.

        Args:
            other: the choices that shall be available
        """
        self._available_choices = other

    @property
    def option_descriptions(self) -> dict[int, str]:
        """
        Return the option descriptions.

        Returns:
            the option descriptions
        """
        return self._option_descriptions

    @option_descriptions.setter
    def option_descriptions(self, descriptions: dict[int, str]) -> None:
        """
        Set the option descriptions.

        Args:
            descriptions: a dict [relationship_type.pk, relationship_type.description]
        """
        self._option_descriptions = descriptions

    def create_option(  # noqa: WPS211
        self,
        name: str,
        value: Any,
        label: Union[int, str],
        selected: bool,
        index: int,
        subindex: Optional[int] = None,
        attrs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Initialize an option (choice).

        Disables the option if it is not among the available choices.

        Args:
            name: option name
            value: option value
            label: option label
            selected: selected option
            index: option index
            subindex: option subindex
            attrs: option attributes

        Returns:
            the dict for _available_choices.
        """
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs,
        )
        if value not in self.available_choices:
            option_dict['attrs']['disabled'] = 'disabled'
        option_dict['attrs']['data-title'] = self._option_descriptions[value]
        return option_dict
