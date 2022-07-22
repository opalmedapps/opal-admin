"""This module is used to provide configuration, fixtures, and plugins for pytest within hospital-settings app."""
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import model_to_dict

import pytest

from . import factories
from .forms import InstitutionForm
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


@pytest.fixture(name='institution_form_files')
def fixture_institution_form_files() -> dict:
    """Fixture providing logo images for the InstitutionForm.

    Returns:
        dictionary with two logo image files
    """
    with Path('opal/tests/fixtures/test_logo.png').open(mode='rb') as image_logo:
        file_content = image_logo.read()

    return {
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


@pytest.fixture()
def institution_form(institution_form_files: dict) -> InstitutionForm:
    """Fixture providing data for the `InstitutionForm`.

    Args:
        institution_form_files (dict): dictionary with logo images

    Returns:
        InstitutionForm object
    """
    instit = factories.Institution.build()
    form_data = model_to_dict(instit, exclude=['id', 'logo', 'logo_en', 'logo_fr'])

    return InstitutionForm(
        data=form_data,
        files=institution_form_files,
        instance=instit,
    )


@pytest.fixture()
def incomplete_institution_form(institution_form_files: dict) -> InstitutionForm:
    """Fixture providing data for the incomplete `InstitutionForm`.

    Args:
        institution_form_files (dict): dictionary with logo images

    Returns:
        incomplete InstitutionForm object
    """
    instit = factories.Institution.build()
    form_data = model_to_dict(instit, exclude=['id', 'logo', 'logo_en', 'logo_fr', 'code'])

    return InstitutionForm(
        data=form_data,
        files=institution_form_files,
        instance=instit,
    )
