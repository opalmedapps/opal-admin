"""This module is used to provide configuration, fixtures, and plugins for pytest within hospital-settings app."""
import pytest

from . import factories
from .models import Institution, Site


@pytest.fixture(name='institution')
def institution() -> Institution:
    """Fixture providing an instance of `Institution` model.

    Returns:
        an instance of `Institution`
    """
    return factories.Institution()


@pytest.fixture()
def site() -> Site:
    """Fixture providing an instance of `Site` model.

    Returns:
        an instance of `Site`
    """
    return factories.Site()
