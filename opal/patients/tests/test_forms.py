import datetime
from typing import Tuple, Type

from django.contrib.auth import get_user_model

import pytest

from opal.users.models import User

from .. import factories
from ..forms import (
    ConfirmExistingUserForm,
    ConfirmPasswordForm,
    ConfirmPatientForm,
    ExistingUserForm,
    RequestorAccountForm,
    RequestorDetailsForm,
    SearchForm,
    SelectSiteForm,
)

UserModel: Type[User] = get_user_model()
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


# tuple with valid medical card type and medical number
# will update the test data once the validator is done in another ticket
test_valid_medical_card_type_and_number: list[Tuple] = [
    ('mrn', 'MRNT99996666'),
    ('ramq', 'RAMQ99996666'),
    ('mrn', 'MRNT00001111'),
]


@pytest.mark.parametrize(('card_type', 'card_number'), test_valid_medical_card_type_and_number)
def test_search_form_valid(
    card_type: str,
    card_number: str,
) -> None:
    """Ensure that the search form is valid."""
    form_data = {
        'medical_card': card_type,
        'medical_number': card_number,
    }
    form = SearchForm(data=form_data)
    assert form.is_valid()


# tuple with invalid medical card type and medical number
test_invalid_medical_card_type_and_number: list[Tuple] = [
    ('ramq', 'ramq99996666'),
]


@pytest.mark.parametrize(('card_type', 'card_number'), test_invalid_medical_card_type_and_number)
def test_search_form_invalid_ramq_field(
    card_type: str,
    card_number: str,
) -> None:
    """Ensure that the search form is valid."""
    form_data = {
        'medical_card': card_type,
        'medical_number': card_number,
    }
    form = SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['Enter a valid RAMQ number consisting of 4 letters followed by 8 digits']


def test_is_correct_checked() -> None:
    """Ensure that the 'Correct?' checkbox is checked."""
    form_data = {
        'is_correct': True,
    }

    form = ConfirmPatientForm(data=form_data)

    assert form.is_valid()


def test_is_correct_not_checked() -> None:
    """Ensure that the 'Correct?' checkbox is not checked."""
    form_data = {
        'is_correct': False,
    }

    form = ConfirmPatientForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['is_correct'] == ['This field is required.']


def test_disabled_option_exists() -> None:
    """Ensure that a disabled option exists."""
    types = [
        factories.RelationshipType(name='Self', start_age=1),
        factories.RelationshipType(name='Guardian-Caregiver', start_age=14, end_age=18),
        factories.RelationshipType(name='Parent or Guardian', start_age=1, end_age=14),
        factories.RelationshipType(name='Mandatary', start_age=1, end_age=18),
    ]
    form_data = {
        'relationship_type': types,
    }
    form = RequestorDetailsForm(
        data=form_data,
        date_of_birth=datetime.datetime(2004, 1, 1, 9, 20, 30),
    )

    options = form.fields['relationship_type'].widget.options('relationship-type', '')
    for index, option in enumerate(options):
        if index == 3:
            assert 'disabled' not in option['attrs']
        else:
            assert option['attrs']['disabled'] == 'disabled'

    assert list(form.fields['relationship_type'].widget.available_choices) == [
        types[0].pk,
    ]


def test_requestor_account_form_valid() -> None:
    """Ensure that the requestor account form is valid."""
    form_data = {
        'user_type': 1,
    }
    form = RequestorAccountForm(data=form_data)
    assert form.is_valid()


def test_requestor_account_form_invalid() -> None:
    """Ensure that the requestor account form is not valid."""
    form_data = {
        'user_type': '',
    }

    form = SelectSiteForm(data=form_data)

    assert not form.is_valid()


def test_existing_user_form_phone_field_error() -> None:
    """Ensure that the existing user form phone field has error."""
    form_data = {
        'user_email': 'marge.simpson@gmail.com',
        'user_phone': '5141111111',
    }

    form = ExistingUserForm(data=form_data)

    assert not form.is_valid()
    assert form.errors['user_phone'] == [
        'Enter a valid phone number having the format: '
        + '+<countryCode><phoneNumber> (for example +15141234567) '
        + 'with an optional extension "x123"',
    ]


def test_existing_user_form_email_field_error() -> None:
    """Ensure that the existing user form email field has error."""
    form_data = {
        'user_email': 'marge.simpson',
        'user_phone': '5141111111',
    }

    form = ExistingUserForm(data=form_data)

    assert not form.is_valid()
    assert form.errors['user_email'] == ['Enter a valid email address.']


def test_both_checkbox_checked() -> None:
    """Ensure that the `Correct?` and `ID Checked?` checkboxes are checked."""
    form_data = {
        'is_correct': True,
        'is_id_checked': True,
    }

    form = ConfirmExistingUserForm(data=form_data)
    assert form.is_valid()


def test_correct_is_not_checked() -> None:
    """Ensure that the `Correct?` is not checked."""
    form_data = {
        'is_correct': False,
        'is_id_checked': True,
    }

    form = ConfirmExistingUserForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['is_correct'] == ['This field is required.']


def test_id_checked_is_not_checked() -> None:
    """Ensure that the `ID Checked?` is not checked."""
    form_data = {
        'is_correct': True,
        'is_id_checked': False,
    }

    form = ConfirmExistingUserForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['is_id_checked'] == ['This field is required.']


def test_confirm_password_form_valid() -> None:
    """Ensure that the confirm user password form is valid."""
    form_data = {
        'confirm_password': 'test-password',
    }
    user = UserModel.objects.create()
    user.set_password(form_data['confirm_password'])

    form = ConfirmPasswordForm(data=form_data, authorized_user=user)

    assert form.is_valid()


def test_confirm_password_form_password_invalid() -> None:
    """Ensure that user password is not valid."""
    form_data = {
        'confirm_password': 'test-password',
    }
    user = UserModel.objects.create()
    user.set_password('password')

    form = ConfirmPasswordForm(data=form_data, authorized_user=user)

    assert form.errors['confirm_password'] == ['The password you entered is incorrect. Please try again.']
    assert not form.is_valid()
