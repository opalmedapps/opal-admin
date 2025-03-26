from datetime import date, datetime
from typing import Optional

from django.forms import HiddenInput, model_to_dict

import pytest
from crispy_forms.utils import render_crispy_form
from dateutil.relativedelta import relativedelta
from pytest_mock.plugin import MockerFixture

from opal.caregivers.factories import CaregiverProfile
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData
from opal.users.factories import Caregiver
from opal.users.models import User

from .. import constants, factories, forms
from ..filters import ManageCaregiverAccessFilter
from ..models import PREDEFINED_ROLE_TYPES, Relationship, RelationshipStatus, RelationshipType, RoleType
from ..tables import ExistingUserTable

pytestmark = pytest.mark.django_db

OIE_PATIENT_DATA = OIEPatientData(
    date_of_birth=date(1986, 10, 1),
    first_name='Marge',
    last_name='Simpson',
    sex='F',
    alias='',
    ramq='SIMM86600199',
    deceased=False,
    death_date_time=None,
    ramq_expiration=datetime.fromisoformat('2024-01-31 23:59:59'),
    mrns=[
        OIEMRNData(site='MGH', mrn='9999993', active=True),
    ],
)


def test_relationshippending_form_is_valid() -> None:
    """Ensure that the `RelationshipPendingAccess` form is valid."""
    relationship_info = factories.Relationship.create(reason='REASON')
    form_data = model_to_dict(relationship_info)
    # add first_name and last_name as they are not part of the relationship form
    form_data['first_name'] = 'test_firstname'
    form_data['last_name'] = 'test_lastname'

    relationshippending_form = forms.RelationshipAccessForm(
        data=form_data,
        instance=relationship_info,
    )
    assert relationshippending_form.is_valid()


def test_relationshippending_missing_startdate() -> None:
    """Ensure that the `RelationshipPendingAccess` form checks for a missing start date field."""
    relationship_type = RelationshipType.objects.guardian_caregiver()
    relationship_info = factories.Relationship.build(
        patient=factories.Patient(
            date_of_birth=date.today() - relativedelta(
                years=14,
            ),
        ),
        type=relationship_type,
    )
    form_data = model_to_dict(relationship_info, exclude=[
        'start_date',
        'end_date',
    ])

    relationshippending_form = forms.RelationshipAccessForm(
        data=form_data,
        instance=relationship_info,
    )

    assert not relationshippending_form.is_valid()


def test_relationshippending_update() -> None:
    """Ensure that a valid `RelationshipPendingAccess` form can be saved."""
    relationship_info = factories.Relationship.create(reason='REASON')
    form_data = model_to_dict(relationship_info)
    # add first_name and last_name as they are not part of the relationship form
    form_data['first_name'] = 'test_firstname'
    form_data['last_name'] = 'test_lastname'

    relationshippending_form = forms.RelationshipAccessForm(
        data=form_data,
        instance=relationship_info,
    )

    relationshippending_form.save()

    assert Relationship.objects.all()[0].start_date == relationshippending_form.data['start_date']


def test_relationshippending_update_fail() -> None:
    """Ensure that the `RelationshipPendingAccess` form checks for a missing start date field."""
    relationship_type = RelationshipType.objects.guardian_caregiver()
    relationship_info = factories.Relationship.build(
        patient=factories.Patient(
            date_of_birth=date.today() - relativedelta(
                years=14,
            ),
        ),
        type=relationship_type,
    )
    form_data = model_to_dict(relationship_info, exclude=[
        'start_date',
        'end_date',
    ])

    message = 'This field is required.'
    relationshippending_form = forms.RelationshipAccessForm(
        data=form_data,
        instance=relationship_info,
    )

    assert not relationshippending_form.is_valid()
    assert relationshippending_form.errors['start_date'][0] == message


def test_relationshippending_form_date_validated() -> None:
    """Ensure that the `RelationshipPendingAccess` form is validated for startdate>enddate."""
    relationship_type = RelationshipType.objects.guardian_caregiver()
    relationship_info = factories.Relationship.build(
        patient=factories.Patient(
            date_of_birth=date.today() - relativedelta(
                years=14,
            ),
        ),
        caregiver=factories.CaregiverProfile(),
        type=relationship_type,
        start_date=date(2022, 6, 1),
        end_date=date(2022, 5, 1),
    )
    form_data = model_to_dict(relationship_info)

    message = 'Start date should be earlier than end date.'
    relationshippending_form = forms.RelationshipAccessForm(
        data=form_data,
        instance=relationship_info,
    )

    assert not relationshippending_form.is_valid()
    assert relationshippending_form.errors['start_date'][0] == message


def test_relationship_pending_status_reason() -> None:
    """Ensure that the `RelationshipPendingAccess` form is validated for reason is not empty when status is denied."""
    relationship_type = RelationshipType.objects.guardian_caregiver()
    relationship_info = factories.Relationship.build(
        patient=factories.Patient(
            date_of_birth=date.today() - relativedelta(
                years=14,
            ),
        ),
        caregiver=factories.CaregiverProfile(),
        type=relationship_type,
        status=RelationshipStatus.DENIED,
        start_date=date(2022, 5, 1),
        end_date=date(2022, 6, 1),
        reason='',
    )
    form_data = model_to_dict(relationship_info)

    message = 'Reason is mandatory when status is denied or revoked.'
    pending_form = forms.RelationshipAccessForm(
        data=form_data,
        instance=relationship_info,
    )

    assert not pending_form.is_valid()
    assert pending_form.errors['reason'][0] == message


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
        'medical_card': constants.MedicalCard.MRN.name,
        'medical_number': '',
        'site_code': 'RVH',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()

    assert 'This field is required.' in form.errors['medical_number']
    assert form.non_field_errors()[0] == 'Provided MRN or site is invalid.'


def test_find_patient_by_mrn_invalid_site_code() -> None:
    """Ensure that the `find_patient_by_mrn` catch an error with an invalid site code."""
    form_data = {
        'medical_card': constants.MedicalCard.MRN.name,
        'medical_number': '9999996',
        'site_code': '',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.non_field_errors()[0] == 'Provided MRN or site is invalid.'


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
                'message': 'Could not establish a connection to the hospital interface.',
            },
        },
    )

    form_data = {
        'medical_card': constants.MedicalCard.MRN.name,
        'medical_number': '9999993',
        'site_code': 'MGH',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.non_field_errors()[0] == 'Could not establish a connection to the hospital interface.'


def test_find_patient_by_mrn_success(mocker: MockerFixture) -> None:
    """
    Ensure that the form is valid by returning the expected OIE data structure.

    Mock find_patient_by_mrn and pretend it was successful
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_mrn',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA._asdict(),
        },
    )

    form_data = {
        'medical_card': constants.MedicalCard.MRN.name,
        'medical_number': '9999993',
        'site_code': 'MGH',
    }

    form = forms.SearchForm(data=form_data)
    assert form.is_valid()


def test_find_patient_by_ramq_invalid_ramq() -> None:
    """Ensure that the `find_patient_by_ramq` catch an error with an invalid site ramq."""
    form_data = {
        'medical_card': constants.MedicalCard.RAMQ.name,
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
                'message': 'Could not establish a connection to the hospital interface.',
            },
        },
    )

    form_data = {
        'medical_card': constants.MedicalCard.RAMQ.name,
        'medical_number': 'RAMQ99996666',
    }

    form = forms.SearchForm(data=form_data)
    assert not form.is_valid()
    assert form.non_field_errors()[0] == 'Could not establish a connection to the hospital interface.'


def test_find_patient_by_ramq_success(mocker: MockerFixture) -> None:
    """
    Ensure that the form is valid by returning the expected OIE data structure.

    Mock find_patient_by_ramq and pretend it was successful
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA._asdict(),
        },
    )

    form_data = {
        'medical_card': constants.MedicalCard.RAMQ.name,
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
        'relationship_type': factories.RelationshipType(start_age=1, form_required=True),
        'requestor_form': False,
    }

    form = forms.RequestorDetailsForm(
        data=form_data,
        ramq='MARG99991313',
        mrn='9999993',
        site='MGH',
        date_of_birth=date.today() - relativedelta(
            years=14,
        ),
    )
    assert not form.is_valid()
    assert form.errors['requestor_form'] == ['Form request is required.']


def test_disabled_option_exists() -> None:
    """Ensure that a disabled option exists."""
    self_type = RelationshipType.objects.self_type()
    mandatary_type = RelationshipType.objects.mandatary()
    factories.Patient(ramq='MARG99991313')

    form_data = {
        'relationship_type': RelationshipType.objects.all(),
    }
    form = forms.RequestorDetailsForm(
        data=form_data,
        ramq='MARG99991313',
        mrn='9999993',
        site='MGH',
        date_of_birth=date.today() - relativedelta(
            years=14,
        ),
    )

    options = form.fields['relationship_type'].widget.options('relationship-type', '')
    for option in options:
        if option['label'] in {'Self', 'Mandatary'}:
            assert 'disabled' not in option['attrs']
        else:
            assert option['attrs']['disabled'] == 'disabled'

    assert list(form.fields['relationship_type'].widget.available_choices) == [
        mandatary_type.pk,
        self_type.pk,
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

    form = forms.ExistingUserForm(
        data=form_data,
        relationship_type=factories.RelationshipType(name='Self', start_age=1, form_required=True),
    )

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

    form = forms.ExistingUserForm(
        data=form_data,
        relationship_type=factories.RelationshipType(name='Self', start_age=1, form_required=True),
    )

    assert not form.is_valid()
    assert form.errors['user_email'] == ['Enter a valid email address.']


def test_existing_user_form_user_not_found() -> None:
    """Ensure that the existing user is not found."""
    form_data = {
        'user_email': 'marge.simpson@gmail.com',
        'user_phone': '+15142222222',
    }
    Caregiver(email='marge.simpson@gmail.com', phone_number='+15141111111')

    form = forms.ExistingUserForm(
        data=form_data,
        relationship_type=factories.RelationshipType(name='Self', start_age=1, form_required=True),
    )

    error_message = (
        'Opal user was not found in your database. '
        + 'This may be an out-of-hospital account. '
        + 'Please proceed to generate a new QR code. '
        + 'Inform the user they must register at the Registration website.'
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == error_message


def test_existing_user_not_more_than_one_self() -> None:
    """Ensure that the existing user is not allowed to have more than one self relationship."""
    form_data = {
        'user_email': 'bart.simpson@gmail.com',
        'user_phone': '+15142222222',
    }
    user_caregiver = Caregiver(
        email='bart.simpson@gmail.com',
        phone_number='+15142222222',
        first_name='Bart',
        last_name='Simpson',
    )
    caregiver = CaregiverProfile(user=user_caregiver)
    patient = factories.Patient(first_name='Bart', last_name='Simpson')
    relationship_type = factories.RelationshipType(
        role_type=RoleType.SELF,
        name='Self',
        start_age=1,
        form_required=True,
    )
    factories.Relationship(patient=patient, caregiver=caregiver, type=relationship_type)

    form = forms.ExistingUserForm(
        data=form_data,
        relationship_type=relationship_type,
    )

    error_message = (
        'This opal user already has a self-relationship with the patient.'
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


def test_confirm_password_form_valid(mocker: MockerFixture) -> None:
    """Ensure that the confirm user password form is valid."""
    form_data = {
        'confirm_password': 'test-password',
    }
    user = User.objects.create()
    user.set_password(form_data['confirm_password'])

    # mock fed authentication and pretend it was successful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = ('user@example.com', 'First', 'Last')

    form = forms.ConfirmPasswordForm(data=form_data, authorized_user=user)

    assert form.is_valid()


def test_confirm_password_form_password_invalid(mocker: MockerFixture) -> None:
    """Ensure that user password is not valid."""
    form_data = {
        'confirm_password': 'test-password',
    }
    user = User.objects.create()
    user.set_password('password')

    # mock fed authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = None

    form = forms.ConfirmPasswordForm(data=form_data, authorized_user=user)

    assert form.errors['confirm_password'] == ['The password you entered is incorrect. Please try again.']
    assert not form.is_valid()


# Tests for ManageCaregiverAccessFilter
def test_filter_managecaregiver_missing_site() -> None:
    """Ensure that `site` is required when filtering caregiver access by `mrn`."""
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': '',
        'medical_number': '9999996',
    }
    form = ManageCaregiverAccessFilter(data=form_data)
    assert not form.is_valid()
    assert form.errors['site'] == ['This field is required.']


def test_filter_managecaregiver_missing_mrn() -> None:
    """Ensure that `medical_number` is required when filtering caregiver access by `mrn`."""
    hospital_patient = factories.HospitalPatient()

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': '',
    }
    form = ManageCaregiverAccessFilter(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['This field is required.']


def test_filter_managecaregiver_missing_ramq() -> None:
    """Ensure that `medical_number` is required when filtering caregiver access by `ramq`."""
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
        'medical_number': '',
    }
    form = ManageCaregiverAccessFilter(data=form_data)
    assert not form.is_valid()
    assert form.errors['medical_number'] == ['This field is required.']


def test_filter_managecaregiver_missing_valid_mrn() -> None:
    """Ensure that filtering caregiver access by `mrn` passes when required fields are provided."""
    hospital_patient = factories.HospitalPatient()

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': '9999996',
    }
    form = ManageCaregiverAccessFilter(data=form_data)
    assert form.is_valid()


def test_filter_managecaregiver_valid_ramq() -> None:
    """Ensure that filtering caregiver access by `ramq` does not require `site`."""
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
        'medical_number': 'RAMQ12345678',
    }
    form = ManageCaregiverAccessFilter(data=form_data)
    assert form.is_valid()


# Tests for ManageCaregiverAccessUpdateForm
def test_caregiver_first_last_name_update() -> None:
    """Ensure that `first_name` and `last_name` can be updated through the assigned form."""
    form_data = {
        'first_name': 'TEST_first',
        'last_name': 'TEST_last',
    }
    form = forms.ManageCaregiverAccessUserForm(data=form_data)
    assert form.is_valid()


def test_caregiver_first_last_name_invalid() -> None:
    """Ensure that name validations are in place."""
    longname = ''.join('a' for letter in range(200))
    error_message = 'Ensure this value has at most 150 characters (it has 200).'
    form_data = {
        'first_name': longname,
        'last_name': longname,
    }
    form = forms.ManageCaregiverAccessUserForm(data=form_data)
    assert not form.is_valid()
    assert form.errors['first_name'][0] == error_message
    assert form.errors['last_name'][0] == error_message


# Opal Registration Tests
def test_accessrequestsearchform_ramq() -> None:
    """Ensure that site field is disabled when card type is ramq."""
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
    }
    form = forms.AccessRequestSearchPatientForm(data=form_data)
    site_field = form.fields['site']

    assert site_field.disabled
    assert not site_field.required
    assert not isinstance(form.fields['site'].widget, HiddenInput)
    assert site_field.empty_label == 'Not required'  # type: ignore[attr-defined]


def test_accessrequestsearchform_single_site_mrn() -> None:
    """Ensure that site field is disabled and hidden when there is only one site."""
    site = factories.Site()
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
    }
    form = forms.AccessRequestSearchPatientForm(data=form_data)
    site_field = form.fields['site']

    assert form['site'].value() == site.pk
    assert site_field.disabled
    assert site_field.required
    assert isinstance(site_field.widget, HiddenInput)


def test_accessrequestsearchform_more_than_site() -> None:
    """Ensure that site field is not disabled and not hidden when there is more than one site."""
    site = factories.Site()
    factories.Site()

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': site.pk,
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)
    site_field = form.fields['site']

    assert not site_field.disabled
    assert site_field.required
    assert not isinstance(site_field.widget, HiddenInput)


def test_accessrequestsearchform_ramq_validation_fail() -> None:
    """Ensure that invalid ramq is caught and proper error message is displayed."""
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'abc123',
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)

    assert not form.is_valid()
    assert form.errors['medical_number'][0] == 'Enter a valid RAMQ number consisting of 4 letters followed by 8 digits'


def test_accessrequestsearchform_mrn_validation_fail() -> None:
    """Ensure that missing site and mrn are caught and proper error message is displayed."""
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'medical_number': '',
        'site': '',
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)

    assert not form.is_valid()
    assert form.errors['medical_number'][0] == 'This field is required.'
    assert form.errors['site'][0] == 'This field is required.'


def test_accessrequestsearchform_mrn_found_patient_model() -> None:
    """Ensure that patient is found by mrn in Patient model if it exists."""
    patient = factories.Patient()
    site = factories.Site()
    hospital_patient = factories.HospitalPatient(mrn='9999996', patient=patient, site=site)
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'medical_number': hospital_patient.mrn,
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)
    form.fields['site'].initial = site

    assert form.is_valid()
    # asserting that patient object is found
    assert form.patient == patient


def test_accessrequestsearchform_mrn_fail_oie(mocker: MockerFixture) -> None:
    """
    Ensure that proper error message is displayed in OIE response when search by mrn.

    Mock find_patient_by_mrn and pretend it was failed.
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_mrn',
        return_value={
            'status': 'error',
            'data': {
                'message': 'Could not establish a connection to the hospital interface.',
            },
        },
    )
    site = factories.Site()
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'medical_number': '9999993',
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)
    form.fields['site'].initial = site

    assert not form.is_valid()
    assert form.non_field_errors()[0] == 'Could not establish a connection to the hospital interface.'


def test_accessrequestsearchform_mrn_success_oie(mocker: MockerFixture) -> None:
    """
    Ensure that patient is found by mrn and returned by oie if it exists.

    Mock find_patient_by_mrn and pretend it was successful
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_mrn',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )

    site = factories.Site(code='MGH')

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'medical_number': '9999993',
        'site': 'MGH',
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)
    form.fields['site'].initial = site

    assert form.is_valid()
    # assert that data come from OIE in case patient is not found in Patient model
    assert form.patient == OIE_PATIENT_DATA


def test_accessrequestsearchform_ramq_found_patient_model() -> None:
    """Ensure that patient is found by ramq in Patient model if it exists."""
    patient = factories.Patient(ramq='RAMQ12345678')
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': patient.ramq,
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)

    assert form.is_valid()
    # asserting that patient object is found
    assert form.patient == patient


def test_accessrequestsearchform_ramq_fail_oie(mocker: MockerFixture) -> None:
    """
    Ensure that proper error message is displayed in OIE response when search by ramq.

    Mock find_patient_by_mrn and pretend it was failed.
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'error',
            'data': {
                'message': 'Could not establish a connection to the hospital interface.',
            },
        },
    )

    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'TESS53510111',
    }
    form = forms.AccessRequestSearchPatientForm(data=form_data)

    assert not form.is_valid()
    assert form.non_field_errors()[0] == 'Could not establish a connection to the hospital interface.'


def test_accessrequestsearchform_ramq_success_oie(mocker: MockerFixture) -> None:
    """
    Ensure that patient is found by ramq and returned by oie if it exists.

    Mock find_patient_by_mrn and pretend it was successful
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )

    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'TESS53510111',
    }

    form = forms.AccessRequestSearchPatientForm(data=form_data)

    assert form.is_valid()
    # assert that data come from OIE in case patient is not found in Patient model
    assert form.patient == OIE_PATIENT_DATA


# skip until OIE is fixed
@pytest.mark.skip()
def test_accessrequestsearchform_no_patient_found(mocker: MockerFixture) -> None:
    """Ensure that the validation fails if no patient was found."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': '400',
            'data': {'message': 'Bad request'},
        },
    )

    data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'TESS53510111',
    }
    form = forms.AccessRequestSearchPatientForm(data=data)

    assert not form.is_valid()
    assert form.patient is None
    assert form.non_field_errors()[0] == 'No patient could be found.'


def test_accessrequestrequestorform_form_filled_default() -> None:
    """Ensure the form_filled dynamic field can handle an empty value to initialize."""
    form = forms.AccessRequestRequestorForm(patient=OIE_PATIENT_DATA)

    assert form._form_required()
    assert form.fields['form_filled'].required


@pytest.mark.parametrize('role_type', PREDEFINED_ROLE_TYPES)
def test_accessrequestrequestorform_form_filled_required_type(role_type: RoleType) -> None:
    """Ensure the form_filled dynamic field has the correct required value based on the selected relationship type."""
    relationship_type = RelationshipType.objects.get(role_type=role_type)

    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'relationship_type': relationship_type.pk,
        },
    )

    assert form._form_required() == relationship_type.form_required
    assert form.fields['form_filled'].required == relationship_type.form_required


@pytest.mark.parametrize(('age', 'enabled_options'), [
    (13, [RoleType.PARENT_GUARDIAN, RoleType.MANDATARY]),
    (14, [RoleType.GUARDIAN_CAREGIVER, RoleType.MANDATARY, RoleType.SELF]),
    (18, [RoleType.SELF, RoleType.MANDATARY]),
])
def test_accessrequestrequestorform_relationship_type(age: int, enabled_options: list[RoleType]) -> None:
    """Ensure the relationship_type field has the correct options enabled/disabled based on the patient's age."""
    relationship_types = list(
        RelationshipType.objects.filter(
            role_type__in=enabled_options,
        ).values_list('name', flat=True),
    )

    patient = OIE_PATIENT_DATA._asdict()
    patient['date_of_birth'] = date.today() - relativedelta(years=age)
    form = forms.AccessRequestRequestorForm(
        patient=OIEPatientData(**patient),
    )

    options = form.fields['relationship_type'].widget.options('relationship-type', '')
    actual_enabled = [
        option['label']
        for option in options
        if option['attrs'].get('disabled', '') != 'disabled'
    ]

    assert len(actual_enabled) == len(relationship_types)
    assert actual_enabled == relationship_types


def test_accessrequestrequestorform_relationship_type_existing_self() -> None:
    """Ensure that the self option is disabled when the patient already has a self relationship."""
    patient = factories.Patient()
    factories.Relationship(patient=patient, type=RelationshipType.objects.self_type())

    form = forms.AccessRequestRequestorForm(
        patient=patient,
    )

    options = form.fields['relationship_type'].widget.options('relationship-type', '')
    disabled_options = [
        option['label']
        for option in options
        if option['attrs'].get('disabled', '') == 'disabled'
    ]

    disabled_types = list(
        RelationshipType.objects.filter(
            role_type__in=[
                RoleType.SELF,
                RoleType.GUARDIAN_CAREGIVER,
                RoleType.PARENT_GUARDIAN,
            ],
        ).values_list('name', flat=True),
    )

    assert disabled_options == disabled_types


@pytest.mark.parametrize('user_type', [
    None,
    constants.UserType.NEW.name,
    constants.UserType.EXISTING.name,
])
def test_accessrequestrequestorform_is_existing_user_selected(user_type: Optional[str]) -> None:
    """Ensure the existing user is not selected by default."""
    data = None

    if user_type:
        data = {'user_type': user_type}

    form = forms.AccessRequestRequestorForm(patient=OIE_PATIENT_DATA, data=data)

    expected_type = user_type or constants.UserType.NEW.name
    is_existing_user_selected = user_type == constants.UserType.EXISTING.name
    assert form.is_existing_user_selected() == is_existing_user_selected
    assert form['user_type'].value() == expected_type


def test_accessrequestrequestorform_is_existing_user_selected_cleaned_data() -> None:
    """Ensure the existing user is not selected by default."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'user_type': constants.UserType.EXISTING.name},
    )
    form.full_clean()

    assert form.is_existing_user_selected(form.cleaned_data)


def test_accessrequestrequestorform_new_user_required_fields() -> None:
    """Ensure the new user fields are required."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
    )

    assert form.fields['first_name'].required
    assert form.fields['last_name'].required
    assert not form.fields['user_email'].required
    assert not form.fields['user_phone'].required


def test_accessrequestrequestorform_new_user_layout() -> None:
    """Ensure the new user fields are shown."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
    )

    html = render_crispy_form(form)
    assert '<input type="text" name="first_name"' in html
    assert '<input type="text" name="last_name"' in html
    assert '<input type="text" name="user_email"' not in html
    assert '<input type="text" name="user_phone"' not in html


def test_accessrequestrequestorform_existing_user_required_fields() -> None:
    """Ensure the existing user fields are required."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'user_type': constants.UserType.EXISTING.name},
    )

    assert not form.fields['first_name'].required
    assert not form.fields['last_name'].required
    assert form.fields['user_email'].required
    assert form.fields['user_phone'].required


def test_accessrequestrequestorform_existing_user_layout() -> None:
    """Ensure the new user fields are shown."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'user_type': constants.UserType.EXISTING.name},
    )

    html = render_crispy_form(
        form,
        context={'user_table': ExistingUserTable(data=[])},
    )
    assert '<input type="text" name="first_name"' not in html
    assert '<input type="text" name="last_name"' not in html
    assert '<input type="email" name="user_email"' in html
    assert '<input type="text" name="user_phone"' in html


def test_accessrequestrequestorform_existing_user_search_not_found() -> None:
    """Ensure an error is shown when no existing user is found."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == 'No existing user could be found.'


def test_accessrequestrequestorform_existing_user_no_data() -> None:
    """Ensure `clean()` can handle non-existent user email and phone fields."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
        },
    )

    assert not form.is_valid()


def test_accessrequestrequestorform_existing_user_empty_data() -> None:
    """Ensure `clean()` can handle empty user email and phone fields."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'user_email': '',
            'user_phone': '',
        },
    )

    assert not form.is_valid()


def test_accessrequestrequestorform_existing_user_found() -> None:
    """Ensure `clean()` finds an existing caregiver."""
    caregiver = CaregiverProfile(
        user__first_name='Marge',
        user__last_name='Simpson',
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )

    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.mandatary(),
            'form_filled': True,
            'id_checked': True,
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
    )

    print(form.errors)
    assert form.is_valid()
    assert form.existing_user == caregiver


def test_accessrequestrequestorform_existing_user_validate_self() -> None:
    """Ensure `clean()` validates a self relationship to match names."""
    caregiver = CaregiverProfile(
        user__first_name='Marge',
        user__last_name='Simpson',
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )

    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
    )

    assert form.is_valid()
    assert form.existing_user == caregiver


def test_accessrequestrequestorform_existing_user_validate_self_name_mismatch() -> None:
    """Ensure `clean()` can handle a name mismatch for self relationships."""
    CaregiverProfile(
        user__first_name='Ned',
        user__last_name='Flanders',
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )

    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == (
        'A self-relationship was selected but the caregiver appears to be someone other than the patient.'
    )


def test_accessrequestrequestorform_existing_user_validate_self_patient_exists() -> None:
    """Ensure `clean()` handles an existing patient already having a self relationship."""
    caregiver = Caregiver(
        first_name='Marge',
        last_name='Simpson',
        email='marge@opalmedapps.ca',
        phone_number='+15141234567',
    )
    relationship = factories.Relationship(
        patient__first_name='Marge',
        patient__last_name='Simpson',
        caregiver=CaregiverProfile(user=caregiver),
        type=RelationshipType.objects.self_type(),
    )

    form = forms.AccessRequestRequestorForm(
        patient=relationship.patient,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'user_email': caregiver.email,
            'user_phone': caregiver.phone_number,
        },
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == (
        'The patient already has a self-relationship'
    )


def test_accessrequestrequestorform_existing_user_validate_self_caregiver_exists() -> None:
    """Ensure `clean()` handles an existing caregiver already having a self relationship."""
    caregiver = Caregiver(
        first_name='Marge',
        last_name='Simpson',
        email='marge@opalmedapps.ca',
        phone_number='+15141234567',
    )
    factories.Relationship(
        patient__first_name='Marge',
        patient__last_name='Simpson',
        caregiver=CaregiverProfile(user=caregiver),
        type=RelationshipType.objects.self_type(),
    )

    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'user_email': caregiver.email,
            'user_phone': caregiver.phone_number,
        },
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == (
        'The caregiver already has a self-relationship'
    )


def test_accessrequestrequestorform_existing_user_relationship_exists() -> None:
    """Ensure clean handles a caregiver already having a CONFIRMED or PENDING relationship to the patient."""
    caregiver = Caregiver(
        first_name='Marge',
        last_name='Simpson',
        email='marge@opalmedapps.ca',
        phone_number='+15141234567',
    )
    relationship = factories.Relationship(
        caregiver=CaregiverProfile(user=caregiver),
        type=RelationshipType.objects.mandatary(),
        status=RelationshipStatus.CONFIRMED,
    )

    form = forms.AccessRequestRequestorForm(
        patient=relationship.patient,
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.guardian_caregiver(),
            'form_filled': True,
            'id_checked': True,
            'user_email': caregiver.email,
            'user_phone': caregiver.phone_number,
        },
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == (
        'There already exists an active relationship between the patient and caregiver.'
    )


def test_accessrequestrequestorform_first_last_name_not_disabled() -> None:
    """Ensure that the first and last name are not disabled for no selection."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
    )

    assert not form.fields['first_name'].disabled
    assert not form.fields['last_name'].disabled


def test_accessrequestrequestorform_first_last_name_not_disabled_selection() -> None:
    """Ensure that the first and last name are not disabled for a non-self relationship type selection."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'relationship_type': RelationshipType.objects.mandatary().pk},
    )

    assert not form.fields['first_name'].disabled
    assert not form.fields['last_name'].disabled


def test_accessrequestrequestorform_first_last_name_disabled() -> None:
    """Ensure that the first and last name are disabled when self is selected."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'relationship_type': RelationshipType.objects.self_type().pk},
    )

    assert form.fields['first_name'].disabled
    assert form.fields['last_name'].disabled


def test_accessrequestrequestorform_self_names_prefilled() -> None:
    """Ensure the first and last name are pre-filled with the patient's name if self is selected."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'relationship_type': RelationshipType.objects.self_type().pk},
    )

    assert form.fields['first_name'].initial == OIE_PATIENT_DATA.first_name
    assert form['first_name'].value() == OIE_PATIENT_DATA.first_name
    assert form.fields['last_name'].initial == OIE_PATIENT_DATA.last_name
    assert form['last_name'].value() == OIE_PATIENT_DATA.last_name


def test_accessrequestrequestorform_self_names_prefilled_empty_initial() -> None:
    """Ensure the name fields are filled with the patient's name even if the initial data contains empty strings."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'relationship_type': RelationshipType.objects.self_type().pk},
        # this happens when switching to self due to the up-validate request handling
        initial={'first_name': '', 'last_name': ''},
    )

    assert form.fields['first_name'].initial == OIE_PATIENT_DATA.first_name
    assert form['first_name'].value() == OIE_PATIENT_DATA.first_name
    assert form.fields['last_name'].initial == OIE_PATIENT_DATA.last_name
    assert form['last_name'].value() == OIE_PATIENT_DATA.last_name


def test_accessrequestrequestorform_self_names_prefilled_other_initial() -> None:
    """Ensure the name fields are filled with the patient's name even if the initial data contains empty strings."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={'relationship_type': RelationshipType.objects.self_type().pk},
        # this happens when switching to self due to the up-validate request handling
        initial={'first_name': 'Hans', 'last_name': 'Wurst'},
    )

    assert form.fields['first_name'].initial == OIE_PATIENT_DATA.first_name
    assert form['first_name'].value() == 'Hans'
    assert form.fields['last_name'].initial == OIE_PATIENT_DATA.last_name
    assert form['last_name'].value() == 'Wurst'
