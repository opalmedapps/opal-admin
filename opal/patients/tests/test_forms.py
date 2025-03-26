from datetime import date, datetime
from typing import Optional

from django.forms import HiddenInput, model_to_dict
from django.utils import timezone

import pytest
from crispy_forms.utils import render_crispy_form
from dateutil.relativedelta import relativedelta
from pytest_mock.plugin import MockerFixture
from requests.exceptions import RequestException

from opal.caregivers.factories import CaregiverProfile
from opal.hospital_settings import factories as hospital_factories
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData
from opal.services.twilio import TwilioServiceError
from opal.users.factories import Caregiver, User

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
    relationship_info = factories.Relationship(
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
    relationship_info = factories.Relationship(
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
    assert relationshippending_form.fields['type'].queryset  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    'relationship_type', [
        RoleType.GUARDIAN_CAREGIVER,
        RoleType.PARENT_GUARDIAN,
        RoleType.MANDATARY,
    ],
)
def test_relationshippending_type_not_contain_self(relationship_type: Optional[str]) -> None:
    """Ensure that the `type` field does not contain self but contains the relationship type being updated."""
    self_type = RelationshipType.objects.self_type()
    relation_type = RelationshipType.objects.get(role_type=relationship_type)
    relationship_info = factories.Relationship(
        patient=factories.Patient(
            date_of_birth=date.today() - relativedelta(
                years=14,
            ),
        ),
        type=relation_type,
    )
    form_data = model_to_dict(relationship_info)

    relationshippending_form = forms.RelationshipAccessForm(
        data=form_data,
        instance=relationship_info,
    )

    assert self_type not in relationshippending_form.fields['type'].queryset  # type: ignore[attr-defined]
    assert relation_type in relationshippending_form.fields['type'].queryset  # type: ignore[attr-defined]


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


def test_filter_managecaregiver_valid_mrn() -> None:
    """Ensure that filtering caregiver access by `mrn` passes when required fields are provided."""
    hospital_patient = factories.HospitalPatient()
    factories.Site()
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': '9999996',
    }
    form = ManageCaregiverAccessFilter(data=form_data).form
    site_field = form.fields['site']
    card_type_field = form.fields['card_type']

    assert form.is_valid()
    # test that form is defaulted to MRN
    assert card_type_field.initial == constants.MedicalCard.MRN.name
    assert not site_field.disabled
    assert site_field.required
    assert not isinstance(site_field.widget, HiddenInput)
    assert site_field.empty_label == 'Choose...'


def test_form_common_functions_mrn_selected() -> None:
    """Ensure common functions defined reused in forms produce expected results when `MRN` is selected."""
    hospital_patient = factories.HospitalPatient()
    factories.Site()
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': '9999996',
    }
    form = ManageCaregiverAccessFilter(data=form_data).form

    # test functions
    assert forms.is_mrn_selected(form)
    assert not forms.is_not_mrn_or_single_site(form)
    assert forms.get_site_empty_label(form) == 'Choose...'


def test_form_common_functions_mrn_selected_single_site() -> None:
    """Ensure common functions defined reused in forms produce expected results when `MRN` is selected."""
    hospital_patient = factories.HospitalPatient()
    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': '9999996',
    }
    form = ManageCaregiverAccessFilter(data=form_data).form

    # test functions
    assert forms.is_mrn_selected(form)
    assert forms.is_not_mrn_or_single_site(form)


def test_form_common_functions_ramq_selected() -> None:
    """Ensure common functions defined reused in forms produce expected results when `RAMQ` is selected."""
    factories.HospitalPatient()
    factories.Site()
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
        'medical_number': 'RAMQ12345678',
    }
    form = ManageCaregiverAccessFilter(data=form_data).form

    # test functions
    assert not forms.is_mrn_selected(form)
    assert forms.is_not_mrn_or_single_site(form)
    assert forms.get_site_empty_label(form) == 'Not required'


def test_filter_managecaregiver_valid_ramq() -> None:
    """Ensure that filtering caregiver access by `ramq` does not require `site` and disabled it."""
    factories.HospitalPatient()
    factories.Site()

    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
        'medical_number': 'RAMQ12345678',
    }
    form = ManageCaregiverAccessFilter(data=form_data).form
    site_field = form.fields['site']

    assert form.is_valid()
    assert form.cleaned_data['card_type'] == constants.MedicalCard.RAMQ.name
    assert site_field.disabled
    assert not site_field.required
    assert not isinstance(site_field.widget, HiddenInput)
    assert site_field.empty_label == 'Not required'


def test_filter_managecaregiver_valid_ramq_single_site() -> None:
    """Ensure that filtering caregiver access by `ramq` when there is single site, hides `site`."""
    hospital_patient = factories.HospitalPatient()
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'site': '',
        'medical_number': 'RAMQ12345678',
    }
    form = ManageCaregiverAccessFilter(data=form_data).form
    site_field = form.fields['site']
    card_type_field = form.fields['card_type']

    assert card_type_field.initial != constants.MedicalCard.RAMQ.name
    assert form.is_valid()
    # assert value of site is set although the field is hidden
    assert form.cleaned_data['site'] == hospital_patient.site
    assert site_field.disabled
    assert isinstance(site_field.widget, HiddenInput)


def test_filter_managecaregiver_valid_mrn_single_site() -> None:
    """Ensure that filtering caregiver access by `mrn` passes when required fields are provided."""
    hospital_patient = factories.HospitalPatient()

    form_data = {
        'card_type': constants.MedicalCard.MRN.name,
        'site': hospital_patient.site.id,
        'medical_number': '9999996',
    }
    form = ManageCaregiverAccessFilter(data=form_data).form

    site_field = form.fields['site']
    card_type_field = form.fields['card_type']

    assert card_type_field.initial == constants.MedicalCard.MRN.name
    assert form.is_valid()
    # assert value of site is set although the field is hidden
    assert form.cleaned_data['site'] == hospital_patient.site
    assert site_field.disabled
    assert isinstance(site_field.widget, HiddenInput)


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


def test_caregiver_access_form_update_self() -> None:
    """Ensure that `first_name` and `last_name` are readonly, `end_date` is not required and `type` is disabled."""
    self_type = factories.RelationshipType(role_type=RoleType.SELF.name)
    patient = factories.Patient()

    relationship = factories.Relationship(
        patient=patient,
        type=self_type,
        status=RelationshipStatus.CONFIRMED,
    )

    form_data = model_to_dict(relationship)
    form_data['first_name'] = patient.first_name
    form_data['last_name'] = patient.last_name

    form = forms.RelationshipAccessForm(data=form_data, instance=relationship)

    assert form.is_valid()
    form_fields = form.fields

    assert form_fields['first_name'].widget.attrs['readonly']
    assert form_fields['last_name'].widget.attrs['readonly']
    assert form_fields['type'].disabled
    assert form.cleaned_data['type'].role_type == RoleType.SELF.name
    assert not form_fields['end_date'].required


def test_caregiver_access_form_update_self_fail() -> None:
    """Ensure that different patient and caregiver names and non-confirmed status raise error for self-relationship."""
    self_type = factories.RelationshipType(role_type=RoleType.SELF.name)
    patient = factories.Patient()

    relationship = factories.Relationship(
        patient=patient,
        type=self_type,
        status=RelationshipStatus.PENDING,
    )

    form_data = model_to_dict(relationship)
    form_data['first_name'] = 'test_first_name'
    form_data['last_name'] = 'test_last_name'

    diff_name_err = 'A self-relationship was selected but the caregiver appears to be someone other than the patient.'
    pending_err = '"Pending" status does not apply for the Self relationship.'
    form = forms.RelationshipAccessForm(data=form_data, instance=relationship)

    assert not form.is_valid()
    assert diff_name_err in form.errors['__all__']
    assert pending_err in form.errors['status']


def test_caregiver_access_form_update_non_self() -> None:
    """Ensure that non-self `first_name`,`last_name` are editable, `end_date` is required and `type` is enabled."""
    patient = factories.Patient()

    relationship = factories.Relationship(
        patient=patient,
        status=RelationshipStatus.PENDING,
    )

    form_data = model_to_dict(relationship)
    form_data['first_name'] = patient.first_name
    form_data['last_name'] = patient.last_name

    form = forms.RelationshipAccessForm(data=form_data, instance=relationship)

    assert form.is_valid()
    form_fields = form.fields

    assert not form_fields['first_name'].widget.attrs.get('readonly')
    assert not form_fields['last_name'].widget.attrs.get('readonly')
    assert not form_fields['type'].disabled
    assert form_fields['end_date'].required


# Opal Registration Tests
def test_accessrequestsearchform_initial() -> None:
    """Ensure that the card type is the default and the site field is required."""
    form = forms.AccessRequestSearchPatientForm()
    site_field = form.fields['site']

    assert form['card_type'].value() == constants.MedicalCard.MRN.name
    assert not site_field.disabled
    assert site_field.required


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


def test_accessrequestsearchform_ramq_single_site() -> None:
    """Ensure the `Site` field is initialized as expected without setting any value."""
    factories.Site()
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
    }
    form = forms.AccessRequestSearchPatientForm(data=form_data)

    assert form.fields['site'].disabled
    assert not form.fields['site'].initial
    assert isinstance(form.fields['site'].widget, HiddenInput)


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
    assert site_field.empty_label == 'Choose...'  # type: ignore[attr-defined]


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


def test_accessrequestsearchform_search_patient_missing_info(mocker: MockerFixture) -> None:
    """Ensure that `_search_patient` function add error to form when no data is provided."""
    mock_find = mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'success',
            'data': OIE_PATIENT_DATA,
        },
    )
    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'RAMQ12345678',
    }
    form = forms.AccessRequestSearchPatientForm(data=form_data)
    form._search_patient(
        card_type='',
        medical_number='',
        site=None,
    )

    # asserting that correct error message is added to non-field form errors list
    err_msg = 'No patient could be found.'
    assert form.non_field_errors()[0] == err_msg
    mock_find.assert_called_once_with('RAMQ12345678')


def test_accessrequestsearchform_mrn_fail_oie(mocker: MockerFixture) -> None:
    """
    Ensure that error is added if patient is not found in `Patient` model and in `OIE`.

    Mock find_patient_by_mrn and pretend it was failed.
    """
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_mrn',
        return_value={
            'status': 'error',
            'data': {
                'message': ['connection_error'],
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
    assert len(form.non_field_errors()) == 1
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
                'message': ['connection_error'],
            },
        },
    )

    form_data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'TESS53510111',
    }
    form = forms.AccessRequestSearchPatientForm(data=form_data)

    assert not form.is_valid()
    assert len(form.non_field_errors()) == 1
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


def test_accessrequestsearchform_no_patient_found(mocker: MockerFixture) -> None:
    """Ensure that the validation fails if no patient was found."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'error',
            'data': {'message': ['not_found']},
        },
    )

    data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'TESS53510111',
    }
    form = forms.AccessRequestSearchPatientForm(data=data)

    assert not form.is_valid()
    assert form.patient is None
    assert len(form.non_field_errors()) == 1
    assert form.non_field_errors()[0] == 'No patient could be found.'


def test_accessrequestsearchform_no_test_patient(mocker: MockerFixture) -> None:
    """Ensure that the validation fails if the patient is not a test patient."""
    mocker.patch(
        'opal.services.hospital.hospital.OIEService.find_patient_by_ramq',
        return_value={
            'status': 'error',
            'data': {'message': ['no_test_patient']},
        },
    )

    data = {
        'card_type': constants.MedicalCard.RAMQ.name,
        'medical_number': 'TESS53510111',
    }
    form = forms.AccessRequestSearchPatientForm(data=data)

    assert not form.is_valid()
    assert form.patient is None
    assert len(form.non_field_errors()) == 1
    assert form.non_field_errors()[0] == 'Patient is not a test patient.'


def test_accessrequestconfirmpatientform_init() -> None:
    """Ensure that the form is bound for early evaluation."""
    form = forms.AccessRequestConfirmPatientForm(patient=OIE_PATIENT_DATA)

    assert form.is_bound


def test_accessrequestconfirmpatientform_is_deceased_oie() -> None:
    """Ensure that proper error message is added to form error list when oie patient is deceased."""
    oie_patient = OIE_PATIENT_DATA._replace(deceased=True)
    form = forms.AccessRequestConfirmPatientForm(patient=oie_patient)
    err_msg = 'Unable to complete action with this patient. Please contact Medical Records.'

    form.is_valid()

    assert form.non_field_errors()[0] == err_msg


def test_accessrequestconfirmpatientform_is_deceased_patient_model() -> None:
    """Ensure that proper error message is added to form error list when `Patient` model patient is deceased."""
    patient = factories.Patient(date_of_death=timezone.now())

    form = forms.AccessRequestConfirmPatientForm(patient=patient)
    err_msg = 'Unable to complete action with this patient. Please contact Medical Records.'

    form.is_valid()

    assert form.non_field_errors()[0] == err_msg


def test_accessrequestconfirmpatientform_has_multiple_mrns_oie() -> None:
    """Ensure that proper error message is added to form error list when oie patient has more than one `MRN`."""
    oie_patient = OIE_PATIENT_DATA._replace(
        mrns=[
            OIEMRNData(
                site='MCH',
                mrn='9999993',
                active=True,
            ),
            OIEMRNData(
                site='MCH',
                mrn='9999994',
                active=True,
            ),
            OIEMRNData(
                site='RVH',
                mrn='9999993',
                active=True,
            ),
        ],
    )
    form = forms.AccessRequestConfirmPatientForm(patient=oie_patient)
    err_msg = 'Patient has more than one active MRN at the same hospital, please contact Medical Records.'

    form.is_valid()

    assert form.non_field_errors()[0] == err_msg


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
        ).values_list('name', flat=True).reverse(),
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
        ).values_list('name', flat=True).reverse(),
    )

    assert disabled_options == disabled_types


def test_requestor_form_relationship_type_description() -> None:
    """Ensure that the relationship type descriptions are set correctly to AvailableRadioSelect."""
    patient = factories.Patient()
    factories.Relationship(patient=patient, type=RelationshipType.objects.self_type())

    form = forms.AccessRequestRequestorForm(
        patient=patient,
    )

    options = form.fields['relationship_type'].widget.option_descriptions
    assert options[1] == '{0}'.format(
        'The patient is the requestor and is caring for themselves, Age: 14 and older',
    )
    assert options[3] == '{0}{1}'.format(
        'A parent or guardian of a minor who is considered',
        ' incapacitated in terms of self-care, Age: 14-18',
    )


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


@pytest.mark.parametrize('user_type', [
    constants.UserType.NEW,
    constants.UserType.EXISTING,
])
def test_accessrequestrequestorform_validate_user_types(user_type: constants.UserType) -> None:
    """Ensure the form is validated with different `user_types`."""
    relationshiptype = RelationshipType.objects.guardian_caregiver()
    caregiver = factories.CaregiverProfile(
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )
    data = {
        'user_type': user_type.name,
        'relationship_type': relationshiptype.pk,
        'form_filled': True,
        'id_checked': True,
    }

    if user_type == constants.UserType.NEW:
        data.update({
            'first_name': OIE_PATIENT_DATA.first_name,
            'last_name': OIE_PATIENT_DATA.last_name,
        })

    if user_type == constants.UserType.EXISTING:
        data.update({
            'user_email': caregiver.user.email,
            'user_phone': caregiver.user.phone_number,
        })

    form = forms.AccessRequestRequestorForm(patient=OIE_PATIENT_DATA, data=data)

    assert form.is_valid()


def test_accessrequestrequestorform_clean_existing_user_no_type() -> None:
    """Ensure `clean` can handle a missing relationship type."""
    caregiver = factories.CaregiverProfile(
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )
    data = {
        'user_type': constants.UserType.EXISTING.name,
        'form_filled': True,
        'id_checked': True,
        'user_email': caregiver.user.email,
        'user_phone': caregiver.user.phone_number,
    }

    form = forms.AccessRequestRequestorForm(patient=OIE_PATIENT_DATA, data=data)

    assert not form.is_valid()


def test_accessrequestrequestorform_clean_existing_user_no_data() -> None:
    """Ensure `clean` can handle missing data."""
    data = {
        'user_type': constants.UserType.EXISTING.name,
    }

    form = forms.AccessRequestRequestorForm(patient=OIE_PATIENT_DATA, data=data)

    assert not form.is_valid()


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
    """Ensure `clean()` can handle a name mismatch for self relationships for existing users."""
    CaregiverProfile(
        user__first_name='Ned',
        user__last_name='Flanders',
        user__email='marge@opalmedapps.ca',
        user__phone_number='+15141234567',
    )

    form = forms.AccessRequestRequestorForm(
        patient=factories.Patient(),
        data={
            'user_type': constants.UserType.EXISTING.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'user_email': 'marge@opalmedapps.ca',
            'user_phone': '+15141234567',
        },
    )

    assert not form.is_valid()
    assert len(form.non_field_errors()) == 1
    assert form.non_field_errors()[0] == (
        'A self-relationship was selected but the caregiver appears to be someone other than the patient.'
    )


def test_accessrequestrequestorform_new_user_validate_self_name_mismatch() -> None:
    """Ensure the form will ignore provided names for a self relationship."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.NEW.name,
            'relationship_type': RelationshipType.objects.self_type(),
            'id_checked': True,
            'first_name': 'Hans',
            'last_name': 'Wurst',
        },
    )

    assert form.is_valid()
    assert form.cleaned_data['first_name'] == OIE_PATIENT_DATA.first_name
    assert form.cleaned_data['last_name'] == OIE_PATIENT_DATA.last_name


def test_accessrequestrequestorform_existing_user_validate_self_name_mismatch_new_patient() -> None:
    """Ensure `clean()` can handle a name mismatch for self relationships when the patient is new."""
    caregiver = factories.CaregiverProfile(
        user__email='homer@opalmedapps.ca',
        user__phone_number='+15141234567',
        user__first_name='Homer',
    )
    data = {
        'user_type': constants.UserType.EXISTING.name,
        'relationship_type': RelationshipType.objects.self_type(),
        'form_filled': True,
        'id_checked': True,
        'user_email': caregiver.user.email,
        'user_phone': caregiver.user.phone_number,
    }

    form = forms.AccessRequestRequestorForm(patient=OIE_PATIENT_DATA, data=data)

    assert not form.is_valid()
    assert len(form.non_field_errors()) == 1
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
        'The patient already has a self-relationship.'
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
        'The caregiver already has a self-relationship.'
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
    """Ensure the name fields are filled with the patient's name even if the initial data contains data."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        # this happens when switching to self due to the up-validate request handling
        initial={
            'relationship_type': str(RelationshipType.objects.self_type().pk),
            'first_name': 'Hans',
            'last_name': 'Wurst',
        },
    )

    assert form.fields['first_name'].initial == OIE_PATIENT_DATA.first_name
    assert form['first_name'].value() == OIE_PATIENT_DATA.first_name
    assert form.fields['last_name'].initial == OIE_PATIENT_DATA.last_name
    assert form['last_name'].value() == OIE_PATIENT_DATA.last_name


def test_accessrequestrequestorform_non_self_names_prefilled_other_initial() -> None:
    """Ensure the name fields are not filled with any value when it's not self anymore."""
    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={},
        # this happens when switching from self due to the up-validate request handling
        initial={
            'relationship_type': str(RelationshipType.objects.guardian_caregiver().pk),
            'first_name': OIE_PATIENT_DATA.first_name,
            'last_name': OIE_PATIENT_DATA.last_name,
        },
    )

    assert form.fields['first_name'].initial is None
    assert form['first_name'].value() is None
    assert form.fields['last_name'].initial is None
    assert form['last_name'].value() is None


def test_accessrequestrequestorform_disable_fields() -> None:
    """Ensure the `disable_fields` disables all fields in a form."""
    form = forms.AccessRequestRequestorForm(patient=OIE_PATIENT_DATA)

    # disable all fields for the form
    form.disable_fields()

    # assert all fields are disabled
    for _field_name, field in form.fields.items():
        assert field.disabled


def test_accessrequestrequestorform_existing_relationship() -> None:
    """Ensure the `clean()` handles an existing caregiver already having a relationship."""
    caregiver = Caregiver(
        first_name='Test',
        last_name='Caregiver',
        email='test@opalmedapps.ca',
        phone_number='+15141234567',
    )
    factories.Relationship(
        patient__first_name='Marge',
        patient__last_name='Simpson',
        caregiver=CaregiverProfile(user=caregiver),
        type=RelationshipType.objects.mandatary(),
    )

    form = forms.AccessRequestRequestorForm(
        patient=OIE_PATIENT_DATA,
        data={
            'user_type': constants.UserType.NEW.name,
            'relationship_type': RelationshipType.objects.mandatary().pk,
            'id_checked': True,
            'first_name': 'Test',
            'last_name': 'Caregiver',
        },
    )

    assert not form.is_valid()
    assert form.non_field_errors()[0] == 'This Opal user already exists.'


def test_accessrequestconfirmform() -> None:
    """Ensure the confirm form is invalid by default."""
    form = forms.AccessRequestConfirmForm(username='noone')

    assert not form.is_valid()


def test_accessrequestconfirmform_invalid_password(admin_user: User, mocker: MockerFixture) -> None:
    """Ensure that an invalid password fails the form validation."""
    # mock authentication and pretend it was unsuccessful
    mock_authenticate = mocker.patch('opal.core.auth.FedAuthBackend._authenticate_fedauth')
    mock_authenticate.return_value = False

    form = forms.AccessRequestConfirmForm(username=admin_user.username, data={
        'password': 'invalid',
    })

    assert not form.is_valid()
    assert form.has_error('password')


def test_accessrequestconfirmform_valid_password(admin_user: User) -> None:
    """Ensure that a valid user's password makes the form valid."""
    form = forms.AccessRequestConfirmForm(username=admin_user.username, data={
        'password': 'password',
    })

    assert form.is_valid()


def test_accessrequestsendsmsform_incomplete_data(mocker: MockerFixture) -> None:
    """Ensure that the SMS is not sent when the form is incomplete."""
    hospital_factories.Institution()
    mock_send = mocker.patch('opal.services.twilio.TwilioService.send_sms')

    form = forms.AccessRequestSendSMSForm(
        '123456',
        data={
            'language': 'en',
        },
    )

    form.full_clean()

    mock_send.assert_not_called()


def test_accessrequestsendsmsform_send_success(mocker: MockerFixture) -> None:
    """Ensure that the SMS is sent successfully."""
    hospital_factories.Institution()
    mock_send = mocker.patch('opal.services.twilio.TwilioService.send_sms')

    form = forms.AccessRequestSendSMSForm(
        '123456',
        data={
            'language': 'en',
            # magic Twilio number: https://www.twilio.com/docs/iam/test-credentials#test-sms-messages-parameters-To
            'phone_number': '+15005550001',
        },
    )

    form.full_clean()

    mock_send.assert_called_once_with('+15005550001', mocker.ANY)


def test_accessrequestsendsmsform_send_error(mocker: MockerFixture) -> None:
    """Ensure that the form shows an error if sending the SMS failed."""
    hospital_factories.Institution()
    mock_send = mocker.patch(
        'opal.services.twilio.TwilioService.send_sms',
        side_effect=TwilioServiceError('catastrophe!'),
    )

    form = forms.AccessRequestSendSMSForm(
        '123456',
        data={
            'language': 'en',
            # magic Twilio number: https://www.twilio.com/docs/iam/test-credentials#test-sms-messages-parameters-To
            'phone_number': '+15005550001',
        },
    )

    form.full_clean()

    assert not form.is_valid()
    assert len(form.non_field_errors()) == 1
    assert form.non_field_errors()[0] == 'An error occurred while sending the SMS'
    mock_send.assert_called_once_with('+15005550001', mocker.ANY)


def test_accessrequestsendsmsform_send_request_error(mocker: MockerFixture) -> None:
    """Ensure that the form shows an error if the connection to Twilio fails."""
    hospital_factories.Institution()
    mock_send = mocker.patch(
        'opal.services.twilio.TwilioService.send_sms',
        side_effect=RequestException('SSL key too weak'),
    )

    form = forms.AccessRequestSendSMSForm(
        '123456',
        data={
            'language': 'en',
            # magic Twilio number: https://www.twilio.com/docs/iam/test-credentials#test-sms-messages-parameters-To
            'phone_number': '+15005550001',
        },
    )

    form.full_clean()

    assert not form.is_valid()
    assert len(form.non_field_errors()) == 1
    assert form.non_field_errors()[0] == 'An error occurred while sending the SMS'
    mock_send.assert_called_once_with('+15005550001', mocker.ANY)
