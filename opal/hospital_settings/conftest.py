"""This module is used to provide configuration, fixtures, and plugins for pytest within hospital-settings app."""

from typing import Any

import pytest

from .models import Institution


@pytest.fixture()
def institution() -> Any:
    """Fixture providing an instance of ``Institution`` model.

    Returns:
        an instance of ``Institution``
    """
    return Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='TEST1')
