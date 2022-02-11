"""Mocks pytkdocs to workaround issues with Django REST framework."""

from operator import attrgetter
from unittest.mock import MagicMock

from pytkdocs.loader import Loader, split_attr_name

print('mocking pytkdocs to support DRF')

original_add_fields = Loader.add_fields


def add_fields(loader, node, root_object, *args, **kwargs) -> None:
    if not str(root_object).endswith('.Meta.model'):
        original_add_fields(loader, node, root_object, *args, **kwargs)


def detect_field_model(loader, attr_name: str, direct_members, all_members) -> bool:
    first_order_attr_name, remainder = split_attr_name(attr_name)
    if not (
        first_order_attr_name in direct_members
        or (loader.select_inherited_members and first_order_attr_name in all_members)
    ):
        return False

    return not remainder and attrgetter(remainder)(all_members[first_order_attr_name])
    # if remainder and not attrgetter(remainder)(all_members[first_order_attr_name]):
    #     return False
    # return True


Loader.get_marshmallow_field_documentation = lambda *args, **kwargs: MagicMock()
Loader.add_fields = lambda *args, **kwargs: add_fields(*args, **kwargs)
