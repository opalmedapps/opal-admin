import decimal
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile

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

    with Path('opal/hospital_settings/tests/fixtures/test_logo.png').open(mode='rb') as image_logo:
        file_content = image_logo.read()

    files_data = {
        'logo_en': SimpleUploadedFile(
            name='logo_en.png',
            content=file_content,
            content_type='image/png',
        ),
        'logo_fr': SimpleUploadedFile(
            name='logo_fr.png',
            content=file_content,
            content_type='image/png',
        ),
    }

    view = InstitutionCreateUpdateView()
    form = view.get_form_class()(data=form_data, files=files_data)

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
        'longitude': '35.4340000000000000',
        'latitude': '42.4340000000000000',
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
        'longitude': '35.4340000000000000',
        'latitude': '42.4340000000000000',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()


def test_site_create_nonnumeric_location_fields() -> None:
    """Ensure that the form validation captures non-numeric entries for longitude and latitude on creations."""
    institution = factories.Institution()

    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
        'longitude': 'eee',
        'latitude': 'ddd',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()


def test_site_create_with_large_long_lat_fields() -> None:
    """Ensure that the form validation does not accept number exceeds max_length for long/lat on creations."""
    institution = factories.Institution()

    form_data = {
        'name_en': 'TEST1_EN',
        'name_fr': 'TEST1_FR',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': institution.id,
        'longitude': '43435434.455664546456456',
        'latitude': '45645645.5645645645645645645',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data)
    assert not form.is_valid()


def test_site_update() -> None:
    """Ensure that the site update form is valid."""
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
        'longitude': '35.4340000000000000',
        'latitude': '42.4340000000000000',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=site)

    assert form.is_valid()
    form.save()
    site.refresh_from_db()
    assert site.name == 'TEST1_EN'
    assert site.longitude == pytest.approx(decimal.Decimal('35.434'))


def test_site_update_with_missing_field() -> None:
    """Ensure that the site form checks for missing institution field at the moment of updating a site."""
    site = factories.Site()

    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'code': 'TEST1',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'longitude': '35.4340000000000000',
        'latitude': '42.4340000000000000',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=site)

    assert not form.is_valid()


def test_site_update_nonnumeric_location_fields() -> None:
    """Ensure that the site form checks for nonnumeric longitude and latitude on updates."""
    site = factories.Site()
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': site.institution.id,
        'longitude': '4343rre',
        'latitude': '42ere',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=site)

    assert not form.is_valid()


def test_site_update_with_large_long_lat_field() -> None:
    """Ensure that the site form checks for longitude and latitude max_length fields on updates."""
    site = factories.Site()
    form_data = {
        'name_en': 'TEST1_EN_updated',
        'name_fr': 'TEST1_FR_updated',
        'parking_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'parking_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_en': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'direction_url_fr': 'http://127.0.0.1:8000/hospital-settings/site/1/',
        'code': 'TEST1',
        'institution': site.institution.id,
        'longitude': '35.434000000000003455',
        'latitude': '42.43400000005555545445',
    }

    view = SiteCreateUpdateView()
    form = view.get_form_class()(data=form_data, instance=site)

    assert not form.is_valid()
