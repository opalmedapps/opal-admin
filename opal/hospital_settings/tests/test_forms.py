import pytest

from opal.hospital_settings.views import InstitutionCreateView, InstitutionUpdateView, SiteCreateView, SiteUpdateView

from ..models import Institution, Site

pytestmark = pytest.mark.django_db


def test_institution_create() -> None:
    """Ensure that the institution create form is valid."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TST',
    }

    view = InstitutionCreateView()
    form = view.get_form_class()(data=form_data)
    assert form.is_valid()


def test_institution_create_with_missing_code() -> None:
    """Ensure that the institution form checks for missing code field at the moment of creating a new institution."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
    }

    view = InstitutionCreateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()


def test_institution_update() -> None:
    """Ensure that the institution form checks for missing code field at the moment of creating a new institution."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TST',
    }

    view = InstitutionUpdateView()
    form = view.get_form_class()(data=form_data)
    assert form.is_valid()


def test_institution_update_with_missing_field(institution: Institution) -> None:
    """Ensure that the institution form checks for missing code field at the moment of updating an institution."""
    form_data = {
        'name_en': 'TEST1_EN_EDIT',
        'name_fr': 'TEST1_FR_EDIT',
    }

    view = InstitutionUpdateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()


# SITES


def test_site_create(institution: Institution) -> None:
    """Ensure that the site create form is valid."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }

    view = SiteCreateView()
    form = view.get_form_class()(data=form_data)
    assert form.is_valid()


def test_site_create_with_missing_field() -> None:
    """Ensure that the site form checks for missing institution field at the moment of creating a new site."""
    Institution.objects.create(name_en='TEST1_EN', name_fr='TEST1_FR', code='ALL_SITES')
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
    }

    view = SiteCreateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()


def test_site_update(institution: Institution) -> None:
    """Ensure that the site create form is valid."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
    }

    view = SiteUpdateView()
    form = view.get_form_class()(data=form_data)
    assert form.is_valid()


def test_site_update_with_missing_field(site: Site) -> None:
    """Ensure that the site form checks for missing institution field at the moment of updating a site."""
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
    }

    view = SiteUpdateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()
