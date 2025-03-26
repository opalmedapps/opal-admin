import pytest

from opal.hospital_settings.views import InstitutionCreateUpdateView, SiteCreateUpdateView

from .. import factories

pytestmark = pytest.mark.django_db


def test_institution_create() -> None:
    """Ensure that the institution create form is valid."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TST',
    }

    view = InstitutionCreateUpdateView()
    form = view.get_form_class()(data=form_data)

    assert form.is_valid()


def test_institution_create_with_missing_code() -> None:
    """Ensure that the institution form checks for missing code field at the moment of creating a new institution."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
    }

    view = InstitutionCreateUpdateView()
    form = view.get_form_class()(data=form_data)

    assert not form.is_valid()


def test_institution_update() -> None:
    """Ensure that the institution form checks for missing code field at the moment of creating a new institution."""
    institution = factories.Institution()

    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'code': 'TST',
    }

    view = InstitutionCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=institution)

    assert form.is_valid()
    form.save()
    institution.refresh_from_db()
    assert institution.name == 'TEST1_EN'


def test_institution_update_with_missing_field() -> None:
    """Ensure that the institution form checks for missing code field at the moment of updating an institution."""
    institution = factories.Institution()

    form_data = {
        'name_en': 'TEST1_EN_EDIT',
        'name_fr': 'TEST1_FR_EDIT',
    }

    view = InstitutionCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=institution)

    assert not form.is_valid()


# SITES


def test_site_create() -> None:
    """Ensure that the site create form is valid."""
    institution = factories.Institution()

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

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data)

    assert form.is_valid()


def test_site_create_with_missing_field() -> None:
    """Ensure that the site form checks for missing institution field at the moment of creating a new site."""
    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()


def test_site_update() -> None:
    """Ensure that the site create form is valid."""
    site = factories.Site()

    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': site.institution.id,
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=site)

    assert form.is_valid()
    form.save()
    site.refresh_from_db()
    assert site.name == 'TEST1_EN'


def test_site_update_with_missing_field() -> None:
    """Ensure that the site form checks for missing institution field at the moment of updating a site."""
    site = factories.Site()

    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=site)

    assert not form.is_valid()
