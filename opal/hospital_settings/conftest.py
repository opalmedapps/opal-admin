"""This module is used to provide configuration, fixtures, and plugins for pytest within hospital-settings app."""

import pytest

from .models import Institution


@pytest.fixture()
def institution() -> Institution:
    """Fixture providing an instance of ``Institution`` model.

    Returns:
        an instance of ``Institution``
    """
    return Institution.objects.create(  # type: ignore[no-any-return]
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        code='TEST1',
    )
