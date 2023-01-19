from django.core.exceptions import ValidationError
from django.db.utils import DataError, IntegrityError
from django.utils.crypto import get_random_string

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


def test_institution_factory_multiple() -> None:
    """The Institution factory can build multiple default model instances."""
    institution = factories.Institution()
    institution2 = factories.Institution()

    assert institution == institution2


def test_institution_code_unique() -> None:
    """The institution code needs to be unique."""
    factories.Institution(code='MUHC')

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'MUHC'"):
        factories.Institution(name='Another', code='MUHC')


def test_institution_email_required() -> None:
    """Make sure the institution email is required."""
    with assertRaisesMessage(IntegrityError, "Column 'support_email' cannot be null"):
        factories.Institution(support_email=None)


def test_institution_email_format() -> None:
    """Make sure the institution email format is correct."""
    institution = factories.Institution(support_email='MUHC')

    with assertRaisesMessage(ValidationError, 'Enter a valid email address.'):
        institution.full_clean()


def test_institution_email_max_length() -> None:
    """Make sure the institution email length is less than 254 chars."""
    email = '{0}@opal.com'.format(get_random_string(length=254))
    assert len(email) > 254
    with assertRaisesMessage(DataError, "Data too long for column 'support_email' at row 1"):
        factories.Institution(support_email=email)


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


def test_site_factory_multiple() -> None:
    """The Site factory can build multiple default model instances."""
    site = factories.Site()
    site2 = factories.Site()

    assert site != site2
    assert site.institution == site2.institution


def test_site_code_unique() -> None:
    """The institution name needs to be unique."""
    factories.Site(code='MVP')

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'MVP'"):
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
