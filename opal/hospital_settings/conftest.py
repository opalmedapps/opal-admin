"""This module is used to provide configuration, fixtures, and plugins for pytest within hospital-settings app."""

import pytest

from .models import Institution, Site


@pytest.fixture(name='institution')
def fixture_institution() -> Institution:
    """Fixture providing an instance of `Institution` model.

    Returns:
        an instance of `Institution`
    """
    return Institution.objects.create(  # type: ignore[no-any-return]
        name_en='TEST1_EN',
        name_fr='TEST1_FR',
        code='TEST1',
    )


@pytest.fixture()
def site(institution: Institution) -> Site:
    """Fixture providing an instance of `Site` model.

    Args:
        institution (Institution): Request `institution` fixture

    Returns:
        an instance of `Site`
    """
    return Site.objects.create(  # type: ignore[no-any-return]
        name_en='TEST_NAME_EN',
        name_fr='TEST_NAME_FR',
        parking_url_en='http://127.0.0.1:8000/hospital-settings/site/1/fr',
        parking_url_fr='http://127.0.0.1:8000/hospital-settings/site/1/en',
        code='TEST_CODE',
        institution=institution,
    )
