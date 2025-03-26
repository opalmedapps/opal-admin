"""Mocks pytkdocs to workaround issues with Django and Django REST framework."""

from typing import Any
from unittest.mock import MagicMock

from pytkdocs.loader import Loader, ObjectNode, split_attr_name
from pytkdocs.objects import Object

# keep original add_fields in order to be able to call it in certain cases when mocking
original_add_fields = Loader.add_fields
origin_detect_field_model = Loader.detect_field_model


def add_fields(loader: Loader, node: ObjectNode, root_object: Object, *args: Any, **kwargs: Any) -> None:
    """
    Mock the `add_fields` method to not add fields for `Meta` special classes.

    See: https://github.com/mkdocstrings/mkdocstrings/issues/141

    Args:
        loader: the `pytkdocs` loader instance
        node: the current object node
        root_object: the current object
        args: additional arguments
        kwargs: additional keyword arguments
    """
    if not str(root_object).endswith('.Meta.model'):
        original_add_fields(loader, node, root_object, *args, **kwargs)


def detect_field_model(loader: Loader, attr_name: str, direct_members: Any, all_members: Any) -> bool:
    """
    Mock the `detect_field_model` method to ignore errors with factory-boy `DjangoModelFactory`.

    Causes `AttributeError: 'DjangoOptions' object has no attribute 'get_fields'`

    See: https://github.com/mkdocstrings/pytkdocs/issues/142

    Args:
        loader: the `pytkdocs` loader instance
        attr_name: The name of the attribute to detect, can contain dots
        direct_members: The direct members of the class
        all_members: All members of the class

    Returns:
        Whether the attribute is present.
    """
    first_order_attr_name, remainder = split_attr_name(attr_name)

    if remainder and first_order_attr_name in all_members:
        if not hasattr(all_members[first_order_attr_name], remainder):
            return False

    return origin_detect_field_model(loader, attr_name, direct_members, all_members)



# mock in order to avoid missing metadata error caused by Django REST framework
Loader.get_marshmallow_field_documentation = MagicMock()  # type: ignore[assignment]
Loader.add_fields = add_fields  # type: ignore[assignment]
Loader.detect_field_model = detect_field_model  # type: ignore[assignment]
