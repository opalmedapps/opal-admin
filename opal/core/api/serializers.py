"""Collection of serializers for the core ApiViews."""
from typing import Any

from rest_framework import serializers


class DynamicFieldsSerializer(serializers.ModelSerializer):
    """Dynamic fields serializer for models.

    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Display the fields according to the args.

        Args:
            args: Any
            kwargs: Any

        """
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class LanguagesSerializer(serializers.Serializer):
    """Serializer for the settings languages."""

    code = serializers.CharField(min_length=2, max_length=2)
    name = serializers.CharField()
