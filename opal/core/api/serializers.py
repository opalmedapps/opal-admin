# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Collection of serializers for the core ApiViews."""

from typing import Any, TypeVar

from django.db.models import Model

from rest_framework import serializers

_Model = TypeVar('_Model', bound=Model)


class DynamicFieldsSerializer(serializers.ModelSerializer[_Model]):
    """
    Dynamic fields serializer for models.

    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    Reference: https://www.django-rest-framework.org/api-guide/serializers/#example
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


class LanguageSerializer(serializers.Serializer[list[dict[str, Any]]]):
    """Serializer for a supported language."""

    code = serializers.CharField(min_length=2, max_length=2)
    name = serializers.CharField()
