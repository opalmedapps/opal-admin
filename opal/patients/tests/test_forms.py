import pytest

from opal.hospital_settings import factories
from opal.patients.forms import SelectSiteForm

pytestmark = pytest.mark.django_db


def test_site_selection_exist() -> None:
    """Ensure that the site selection is valid."""
    site = factories.Site(name='Montreal General Hospital', code='MGH')
    form_data = {
        'sites': site,
    }

    form = SelectSiteForm(data=form_data)

    assert form.is_valid()


def test_site_selection_not_exist() -> None:
    """Ensure that the empty site selection is not valid."""
    form_data = {
        'sites': '',
    }

    form = SelectSiteForm(data=form_data)

    assert not form.is_valid()
