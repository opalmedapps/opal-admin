# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module is used to provide configuration, fixtures, and plugins for pytest within hospital-settings app."""

from pathlib import Path

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import model_to_dict
from django.test import Client

import pytest

from opal.users.models import User

from . import factories
from .forms import InstitutionForm


@pytest.fixture
def institution_user(client: Client, django_user_model: User) -> User:
    """
    Fixture providing a `User` instance with the `can_manage_institutions` permission.

    Also logs the user into the test client.
    Use this fixture together with the `client` fixture to make authenticated requests.

    Args:
        client: the Django test client instance
        django_user_model: the `User` model used in this project

    Returns:
        a user instance with the `can_manage_institutions` permission
    """
    user: User = django_user_model.objects.create_user(username='test_institution_user')
    permission = Permission.objects.get(codename='can_manage_institutions')
    user.user_permissions.add(permission)

    user.set_password('testpassword')
    user.save()

    client.force_login(user)

    return user


@pytest.fixture
def site_user(client: Client, django_user_model: User) -> Client:
    """
    Fixture provides an instance of [Client][django.test.Client] with a logged in user with site permission.

    Args:
        client: the Django test client instance
        django_user_model: the `User` model used in this project

    Returns:
        an instance of `Client` with a logged in user with `can_manage_sites` permission
    """
    user = django_user_model.objects.create_user(username='test_site_user')
    permission = Permission.objects.get(codename='can_manage_sites')
    user.user_permissions.add(permission)

    client.force_login(user)

    return client


@pytest.fixture(name='institution_form_files')
def fixture_institution_form_files() -> dict[str, SimpleUploadedFile]:
    """
    Fixture providing logo images for the InstitutionForm.

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
        'terms_of_use_en': SimpleUploadedFile(
            name='terms_of_use_en.pdf',
            content=b'test',
            content_type='application/pdf',
        ),
        'terms_of_use_fr': SimpleUploadedFile(
            name='terms_of_use_fr.pdf',
            content=b'test',
            content_type='application/pdf',
        ),
    }


@pytest.fixture
def institution_form(institution_form_files: dict[str, SimpleUploadedFile]) -> InstitutionForm:
    """
    Fixture providing data for the `InstitutionForm`.

    Args:
        institution_form_files (dict): dictionary with logo images

    Returns:
        InstitutionForm object
    """
    instit = factories.Institution.build()
    form_data = model_to_dict(
        instit,
        exclude=[
            'id',
            'logo',
            'terms_of_use',
        ],
    )

    return InstitutionForm(
        data=form_data,
        files=institution_form_files,
        instance=instit,
    )


@pytest.fixture
def incomplete_institution_form(
    institution_form_files: dict[str, SimpleUploadedFile],
) -> InstitutionForm:
    """
    Fixture providing data for the incomplete `InstitutionForm`.

    Args:
        institution_form_files (dict): dictionary with logo images

    Returns:
        incomplete InstitutionForm object
    """
    instit = factories.Institution.build()
    form_data = model_to_dict(
        instit,
        exclude=[
            'id',
            'logo',
            'logo_en',
            'logo_fr',
            'acronym',
            'terms_of_use',
            'terms_of_use_en',
            'terms_of_use_fr',
        ],
    )

    return InstitutionForm(
        data=form_data,
        files=institution_form_files,
        instance=instit,
    )


@pytest.fixture
def institution_form_no_delay_fields(
    institution_form_files: dict[str, SimpleUploadedFile],
) -> InstitutionForm:
    """
    Fixture providing data for the `InstitutionForm` without delay fields.

    Args:
        institution_form_files (dict): dictionary with logo images

    Returns:
        InstitutionForm object without delay fields
    """
    instit = factories.Institution.build()
    form_data = model_to_dict(
        instit,
        exclude=[
            'id',
            'adulthood_age',
            'non_interpretable_lab_result_delay',
            'interpretable_lab_result_delay',
        ],
    )

    return InstitutionForm(
        data=form_data,
        files=institution_form_files,
        instance=instit,
    )
