import pytest

from opal.hospital_settings import factories

from ..forms import SearchForm, SelectSiteForm

pytestmark = pytest.mark.django_db


def test_site_selection_exist() -> None:
    """Ensure that the site seletion is valid."""
    site = factories.Site(name='Montreal General Hospital', code='MGH')
    form_data = {
        'sites': site,
    }

    form = SelectSiteForm(data=form_data)

    assert form.is_valid()


def test_site_selection_not_exist() -> None:
    """Ensure that the empty site seletion is not valid."""
    form_data = {
        'sites': '',
    }

    form = SelectSiteForm(data=form_data)

    assert not form.is_valid()


def test_search_form_valid() -> None:
    """Ensure that the search form is valid."""
    form_data = {
        'medical_card': 'mrn',
        'medical_number': '999996',
    }

    form = SearchForm(data=form_data)

    assert form.is_valid()


def test_search_form_invalid() -> None:
    """Ensure that the search form is invalid."""
    form_data = {
        'medical_card': '',
        'medical_number': '',
    }

    form = SearchForm(data=form_data)

    assert not form.is_valid()
