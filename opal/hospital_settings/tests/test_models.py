from django.db.utils import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from .. import factories
from ..models import Institution, Site

pytestmark = pytest.mark.django_db


# Institution TESTS

def test_institution_factory() -> None:
    """The factory creates a valid `Institution` instance."""
    institution = factories.Institution()
    institution.full_clean()


def test_institution_code_unique() -> None:
    """The institution name needs to be unique."""
    factories.Institution(code='MUHC')

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'MUHC'"):  # type: ignore[arg-type]
        factories.Institution(name='Another', code='MUHC')


def test_institution_string_method() -> None:
    """Ensure that the `__str__` method is defined for the `Institution` model."""
    # Location is abstract and cannot be instantiated directly
    institution = Institution(name='Test Institution')
    assert str(institution) == 'Test Institution'


def test_institution_ordered() -> None:
    """Ensure that the institutions are ordered by name."""
    factories.Institution(name='BTest Institution')
    factories.Institution(name='ATest Institution', code='ATH')

    first = Institution.objects.all()[0]
    assert first.name == 'ATest Institution'


# Site tests

def test_site_factory() -> None:
    """The factory creates a valid `Site` instance."""
    site = factories.Site()
    site.full_clean()


def test_site_code_unique() -> None:
    """The institution name needs to be unique."""
    factories.Site(code='MVP')

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'MVP'"):  # type: ignore[arg-type]
        factories.Site(code='MVP')


def test_site_string_method() -> None:
    """Ensure that the `__str__` method is defined for the `Site` model."""
    site = factories.Site(name='Test Hospital')

    assert str(site) == 'Test Hospital'


def test_site_ordered() -> None:
    """Ensure that the sites are ordered by name."""
    factories.Site(name='Test Site')
    factories.Site(name='ATest Site')

    first = Site.objects.all()[0]

    assert first.name == 'ATest Site'
