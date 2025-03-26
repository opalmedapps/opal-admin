from datetime import datetime
from typing import Type

from django.contrib.auth import get_user_model

import pytest
from pytest_mock.plugin import MockerFixture

from opal.users.factories import Caregiver
from opal.users.models import User

from .. import factories, forms

UserModel: Type[User] = get_user_model()
pytestmark = pytest.mark.django_db
OIE_PATIENT_DATA = dict({
    'dateOfBirth': '1953-01-01 00:00:00',
    'firstName': 'SANDRA',
    'lastName': 'TESTMUSEMGHPROD',
    'sex': 'F',
    'alias': '',
    'ramq': 'TESS53510111',
    'ramqExpiration': '2018-01-31 23:59:59',
    'mrns': [
        {
            'site': 'MGH',
            'mrn': '9999993',
            'active': True,
        },
    ],
})


def test_site_selection_exist() -> None:
    """Ensure that the site selection is valid."""
    site = factories.Site(name='Montreal General Hospital', code='MGH')
    form_data = {
        'sites': site,
    }

    form = forms.SelectSiteForm(data=form_data)

    assert form.is_valid()


def test_site_selection_not_exist() -> None:
    """Ensure that the empty site selection is not valid."""
    form_data = {
        'sites': '',
    }

    form = forms.SelectSiteForm(data=form_data)

    assert not form.is_valid()


def test_find_patient_by_mrn_invalid_mrn() -> None:
    """Ensure that the `find_patient_by_mrn` catch an error with an invalid MRN."""
    form_data = {
        'medical_card': 'mrn',
        'medical_number': '',
        'site_code': 'RVH',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert 'This field is required.' in form.errors['medical_number']
    assert 'Provided MRN or site is invalid.' in form.errors['medical_number']


def test_find_patient_by_mrn_invalid_site_code() -> None:
    """Ensure that the `find_patient_by_mrn` catch an error with an invalid site code."""
    form_data = {
        'medical_card': 'mrn',
        'medical_number': '9999996',
        'site_code': '',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['Provided MRN or site is invalid.']


def test_find_patient_by_mrn_failure(mocker: MockerFixture) -> None:
    """
    Ensure that the form is not valid and return an error message.

    Mock find_patient_by_mrn and pretend it was failed.
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_mrn',
        return_value={
            'status': 'error',
            'data': {
                'message': 'reponse data is invalid',
            },
        },
    )

    form_data = {
        'medical_card': 'mrn',
        'medical_number': '9999993',
        'site_code': 'MGH',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['reponse data is invalid']


def test_find_patient_by_mrn_success(mocker: MockerFixture) -> None:
    """
    Ensure that the form is valid by returning the expected OIE data structure.

    Mock find_patient_by_mrn and pretend it was successful
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_mrn',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )

    form_data = {
        'medical_card': 'mrn',
        'medical_number': '9999993',
        'site_code': 'MGH',
    }

    form = forms.SearchForm(data=form_data)
    assert form.is_valid()


def test_find_patient_by_ramq_invalid_ramq() -> None:
    """Ensure that the `find_patient_by_ramq` catch an error with an invalid site ramq."""
    form_data = {
        'medical_card': 'ramq',
        'medical_number': 'ram99996666',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['Enter a valid RAMQ number consisting of 4 letters followed by 8 digits']


def test_find_patient_by_ramq_failure(mocker: MockerFixture) -> None:
    """
    Ensure that the form is not valid and return an error message.

    Mock find_patient_by_ramq and pretend it was failed.
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'error',
            'data': {
                'message': 'reponse data is invalid',
            },
        },
    )

    form_data = {
        'medical_card': 'ramq',
        'medical_number': 'RAMQ99996666',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['reponse data is invalid']


def test_find_patient_by_ramq_success(mocker: MockerFixture) -> None:
    """
    Ensure that the form is valid by returning the expected OIE data structure.

    Mock find_patient_by_ramq and pretend it was successful
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )

    form_data = {
        'medical_card': 'ramq',
        'medical_number': 'RAMQ99996666',
    }

    form = forms.SearchForm(data=form_data)
    assert form.is_valid()


def test_is_correct_checked() -> None:
    """Ensure that the 'Correct?' checkbox is checked."""
    form_data = {
        'is_correct': True,
    }

    form = forms.ConfirmPatientForm(data=form_data)
    assert form.is_valid()


def test_is_correct_not_checked() -> None:
    """Ensure that the 'Correct?' checkbox is not checked."""
    form_data = {
        'is_correct': False,
    }

    form = forms.ConfirmPatientForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['is_correct'] == ['This field is required.']


def test_requestor_form_not_check_if_required() -> None:
    """Ensure that the 'requestor_form' checkbox is not checked."""
    form_data = {
        'relationship_type': factories.RelationshipType(name='Self', start_age=1, form_required=True),
        'requestor_form': False,
    }

    form = forms.RequestorDetailsForm(
        data=form_data,
        date_of_birth=datetime(2004, 1, 1, 9, 20, 30),
    )
    assert not form.is_valid()
    assert form.errors['requestor_form'] == ['Form request is required.']


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
    form = forms.RequestorDetailsForm(
        data=form_data,
        date_of_birth=datetime(2004, 1, 1, 9, 20, 30),
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
    form = forms.RequestorAccountForm(data=form_data)
    assert form.is_valid()


def test_requestor_account_form_invalid() -> None:
    """Ensure that the requestor account form is not valid."""
    form_data = {
        'user_type': '',
    }

    form = forms.SelectSiteForm(data=form_data)

    assert not form.is_valid()


def test_existing_user_form_phone_field_error() -> None:
    """Ensure that the existing user form phone field has error."""
    form_data = {
        'user_email': 'marge.simpson@gmail.com',
        'user_phone': '5141111111',
    }

    form = forms.ExistingUserForm(data=form_data)

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

    form = forms.ExistingUserForm(data=form_data)

    assert not form.is_valid()
    assert form.errors['user_email'] == ['Enter a valid email address.']


def test_existing_user_form_user_not_found() -> None:
    """Ensure that the existing user is not found."""
    form_data = {
        'user_email': 'marge.simpson@gmail.com',
        'user_phone': '+15142222222',
    }
    Caregiver(email='marge.simpson@gmail.com', phone_number='+15141111111')

    form = forms.ExistingUserForm(data=form_data)
    error_message = (
        'Opal user was not found in your database. '
        + 'This may be an out-of-hospital account. '
        + 'Please proceed to generate a new QR code. '
        + 'Inform the user they must register at the Registration website.'
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == error_message


def test_both_checkbox_checked() -> None:
    """Ensure that the `Correct?` and `ID Checked?` checkboxes are checked."""
    form_data = {
        'is_correct': True,
        'is_id_checked': True,
    }

    form = forms.ConfirmExistingUserForm(data=form_data)
    assert form.is_valid()


def test_correct_is_not_checked() -> None:
    """Ensure that the `Correct?` is not checked."""
    form_data = {
        'is_correct': False,
        'is_id_checked': True,
    }

    form = forms.ConfirmExistingUserForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['is_correct'] == ['This field is required.']


def test_id_checked_is_not_checked() -> None:
    """Ensure that the `ID Checked?` is not checked."""
    form_data = {
        'is_correct': True,
        'is_id_checked': False,
    }

    form = forms.ConfirmExistingUserForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['is_id_checked'] == ['This field is required.']


def test_new_user_form_valid() -> None:
    """Ensure that the `NewUserForm` is valid."""
    form_data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'is_id_checked': True,
    }

    form = forms.NewUserForm(data=form_data)
    assert form.is_valid()


def test_new_user_form_not_valid() -> None:
    """Ensure that the `NewUserForm` is not valid."""
    form_data = {
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'is_id_checked': False,
    }

    form = forms.NewUserForm(data=form_data)
    assert not form.is_valid()


def test_confirm_password_form_valid() -> None:
    """Ensure that the confirm user password form is valid."""
    form_data = {
        'confirm_password': 'test-password',
    }
    user = UserModel.objects.create()
    user.set_password(form_data['confirm_password'])

    form = forms.ConfirmPasswordForm(data=form_data, authorized_user=user)

    assert form.is_valid()


def test_confirm_password_form_password_invalid() -> None:
    """Ensure that user password is not valid."""
    form_data = {
        'confirm_password': 'test-password',
    }
    user = UserModel.objects.create()
    user.set_password('password')

    form = forms.ConfirmPasswordForm(data=form_data, authorized_user=user)

    assert form.errors['confirm_password'] == ['The password you entered is incorrect. Please try again.']
    assert not form.is_valid()
