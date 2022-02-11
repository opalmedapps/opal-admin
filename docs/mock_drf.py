"""
Mocks pytkdocs to workaround issues with Django REST framework.

See: https://github.com/mkdocstrings/mkdocstrings/issues/141
"""

from typing import Any
from unittest.mock import MagicMock

from pytkdocs.loader import Loader, ObjectNode
from pytkdocs.objects import Object

# keep original add_fields in order to be able to call it in certain cases when mocking
original_add_fields = Loader.add_fields


def add_fields(loader: Loader, node: ObjectNode, root_object: Object, *args: Any, **kwargs: Any) -> None:
    """
    Mock the `add_fields` method to not add fields for `Meta` special classes.

    Args:
        loader: the `pytkdocs` loader instance
        node: the current object node
        root_object: the current object
        args: additional arguments
        kwargs: additional keyword arguments
    """
    if not str(root_object).endswith('.Meta.model'):
        original_add_fields(loader, node, root_object, *args, **kwargs)


# mock in order to avoid missing metadata error caused by Django REST framework
Loader.get_marshmallow_field_documentation = MagicMock()  # type: ignore[assignment]
Loader.add_fields = add_fields  # type: ignore[assignment]
