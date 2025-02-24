# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime as dt
import json
import logging
import uuid
from datetime import date, datetime
from http import HTTPStatus
from typing import Any

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

import pytest
import requests
from pytest_django.asserts import assertRaisesMessage
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from opal.caregivers import models as caregiver_models
from opal.caregivers.factories import CaregiverProfile, RegistrationCode
from opal.core.test_utils import RequestMockerTest
from opal.hospital_settings import models as hospital_models
from opal.hospital_settings.factories import Institution, Site
from opal.legacy.factories import LegacyHospitalIdentifierTypeFactory as LegacyHospitalIdentifierType
from opal.legacy.factories import LegacyUserFactory as LegacyUser
from opal.legacy.models import (
    LegacyEducationalMaterial,
    LegacyEducationalMaterialControl,
    LegacyPatient,
    LegacyPatientControl,
    LegacyPatientHospitalIdentifier,
    LegacyQuestionnaire,
    LegacyUserType,
)
from opal.legacy_questionnaires.models import LegacyAnswerQuestionnaire, LegacyQuestionnairePatient
from opal.legacy_questionnaires.models import LegacyQuestionnaire as qdb_LegacyQuestionnaire
from opal.patients import factories as patient_factories
from opal.patients.models import (
    PREDEFINED_ROLE_TYPES,
    HospitalPatient,
    Patient,
    Relationship,
    RelationshipStatus,
    RelationshipType,
    RoleType,
    SexType,
)
from opal.services.integration.schemas import HospitalNumberSchema, PatientSchema, SexTypeSchema
from opal.users import models as user_models
from opal.users.factories import Caregiver, User

from .. import utils

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


PATIENT_DATA = PatientSchema(
    first_name='Marge',
    last_name='Simpson',
    sex=SexTypeSchema.FEMALE,
    date_of_birth=date.fromisoformat('1986-10-01'),
    date_of_death=None,
    health_insurance_number='SIMM86600199',
    mrns=[],
)
MRN_DATA_RVH = HospitalNumberSchema(site='RVH', mrn='9999993')
MRN_DATA_MGH = HospitalNumberSchema(site='MGH', mrn='9999996', is_active=False)


class _MockResponse(requests.Response):
    def __init__(self, status_code: HTTPStatus, data: Any) -> None:
        self.status_code = status_code
        self.data = data or {}
        self.encoding = 'utf-8'

    @property
    def content(self) -> Any:
        return json.dumps(self.data).encode()


@pytest.mark.parametrize(
    ('first_name', 'last_name', 'date_of_birth', 'sex', 'ramq'),
    [
        # one-digit month
        ('Bart', 'Wayne', date(2013, 2, 23), SexType.MALE, 'WAYB13022399'),
        # one-digit day (and female)
        ('Marge', 'Simpson', date(1986, 10, 1), SexType.FEMALE, 'SIMM86600199'),
    ],
)
def test_build_ramq(first_name: str, last_name: str, date_of_birth: date, sex: SexType, ramq: str) -> None:
    """The RAMQ is derived correctly."""
    assert utils.build_ramq(first_name, last_name, date_of_birth, sex) == ramq


def test_update_registration_code_status_success() -> None:
    """Test get registration code and update its status success."""
    registration_code = RegistrationCode.create(status=caregiver_models.RegistrationCodeStatus.NEW)
    utils.update_registration_code_status(registration_code)
    registration_code.refresh_from_db()
    assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED


def test_find_caregiver_success() -> None:
    """Test get caregiver information success."""
    username1 = 'username-1'
    Caregiver.create(username=username1)
    caregiver = utils.find_caregiver(username1)
    assert caregiver is not None
    assert caregiver.username == username1


def test_find_caregiver_failure() -> None:
    """Test find caregiver information failure."""
    username1 = 'username-1'
    username2 = 'username-2'
    Caregiver.create(username=username1)
    caregiver = utils.find_caregiver(username2)
    assert not caregiver


def test_update_caregiver_success() -> None:
    """Test update caregiver information success."""
    email = 'test@example.com'
    phone_number = '+15141112223'
    language = 'fr'
    username = 'username-2'
    user = User.create(email='foo@bar.com', phone_number='+15141112222', language='en', username='username-1')

    utils.update_caregiver(user, email, username, language, phone_number)

    user.refresh_from_db()
    assert user.email == email
    assert user.language == language
    assert user.phone_number == phone_number
    assert user.username == username


def test_update_caregiver_failure() -> None:
    """Test update caregiver information failure."""
    email = 'test@example.com'
    phone_number = '11111112223'
    language = 'en'
    username = 'username-1'
    user = User.create(email='foo@bar.com', phone_number=phone_number, language=language, username=username)

    expected_message = "{'phone_number': ['Enter a valid value.']}"
    with assertRaisesMessage(
        ValidationError,
        expected_message,
    ):
        utils.update_caregiver(user, email, username, language, phone_number)


def test_replace_caregiver() -> None:
    """Test rebuild relationship and remove the skeleton user."""
    phone_number1 = '+15141112222'
    phone_number2 = '+15141112223'
    language1 = 'en'
    language2 = 'fr'
    username1 = 'username-1'
    username2 = 'username-2'
    caregiver = Caregiver.create(phone_number=phone_number1, language=language1, username=username1)
    CaregiverProfile.create(user=caregiver)
    skeleton = Caregiver.create(phone_number=phone_number2, language=language2, username=username2)
    skeleton_profile = CaregiverProfile.create(user=skeleton)
    relationship = patient_factories.Relationship.create(
        caregiver=skeleton_profile,
    )
    utils.replace_caregiver(caregiver, relationship)
    assert relationship.caregiver.user.username == username1
    assert not user_models.Caregiver.objects.filter(username=username2).exists()


def test_update_caregiver_profile_success() -> None:
    """Test update caregiver profile information success."""
    legacy_id1 = 1
    legacy_id2 = 2
    profile = CaregiverProfile.create(legacy_id=legacy_id1)

    utils.update_caregiver_profile(profile, legacy_id2)

    profile.refresh_from_db()
    assert profile.legacy_id == legacy_id2


def test_update_caregiver_profile_failure() -> None:
    """Test update caregiver profile information failure."""
    legacy_id1 = 1
    legacy_id2 = 'Two'
    profile = CaregiverProfile.create(legacy_id=legacy_id1)

    with pytest.raises(ValidationError, match='value must be an integer'):
        utils.update_caregiver_profile(profile, legacy_id2)  # type: ignore[arg-type]


def test_insert_security_answers_success() -> None:
    """Test insert security answers success."""
    caregiver = CaregiverProfile.create()
    security_answers = [
        {
            'question': 'correct?',
            'answer': 'yes',
        },
        {
            'question': 'correct?',
            'answer': 'maybe',
        },
    ]
    utils.insert_security_answers(caregiver, security_answers)
    security_answers_objs = caregiver_models.SecurityAnswer.objects.all()
    assert len(security_answers_objs) == 2


def test_insert_security_answers_failure() -> None:
    """Test insert security answers failure."""
    caregiver = CaregiverProfile.create()
    security_answers: list[dict[str, Any]] = [
        {
            'question': None,
            'answer': 'yes',
        },
        {
            'question': 'correct?',
            'answer': 'maybe',
        },
    ]
    expected_message = "Column 'question' cannot be null"
    with assertRaisesMessage(
        IntegrityError,
        expected_message,
    ):
        utils.insert_security_answers(caregiver, security_answers)


def test_valid_relationship_types_contain_self_role_type() -> None:
    """Get the queryset of valid relationship types contains self role type."""
    patient = patient_factories.Patient.create()

    valid_types = list(utils.valid_relationship_types(patient).values_list('role_type', flat=True))

    assert RoleType.SELF in valid_types
    assert RoleType.MANDATARY in valid_types


def test_valid_relationship_of_self_contain_self_role_type() -> None:
    """Get the queryset of valid relationship types when instance being updated is of self type."""
    patient = patient_factories.Patient.create()

    valid_types = list(
        utils.valid_relationship_types(
            patient,
        ).values_list('role_type', flat=True),
    )

    assert RoleType.SELF in valid_types
    assert RoleType.MANDATARY in valid_types


def test_valid_relationship_types_not_contain_self_role_type() -> None:
    """Get the queryset of valid relationship types doesn't contain self role type."""
    patient = patient_factories.Patient.create()
    patient_factories.Relationship.create(
        patient=patient,
        type=RelationshipType.objects.self_type(),
    )

    valid_types = list(utils.valid_relationship_types(patient).values_list('role_type', flat=True))

    assert RoleType.SELF not in valid_types
    assert RoleType.MANDATARY in valid_types


def test_get_patient_by_ramq_in_success() -> None:
    """Get the patient instance by RAMQ in success."""
    ramq = 'MARG99991313'
    mrn = '9999993'
    site_code = 'MGH'

    patient = patient_factories.Patient.create(ramq=ramq)

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) == patient


def test_get_patient_by_ramq_in_failed() -> None:
    """Get the patient instance by RAMQ in failed."""
    ramq = 'MARG99991313'
    mrn = '9999993'
    site_code = 'MGH'
    patient_factories.Patient.create(ramq='')

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) is None


def test_get_patient_by_mrn_in_success() -> None:
    """Get the patient instance by MRN and site acronym in success."""
    ramq = ''
    mrn = '9999993'
    site_code = 'MGH'
    patient = patient_factories.Patient.create()
    site = Site.create(acronym=site_code)
    patient_factories.HospitalPatient.create(patient=patient, site=site, mrn=mrn)

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) == patient


def test_get_patient_by_mrn_in_failed() -> None:
    """Get the patient instance by MRN and site acronym in failed."""
    ramq = ''
    mrn = '9999993'
    site_code = 'MGH'
    patient = patient_factories.Patient.create()
    site = Site.create(acronym=site_code)
    patient_factories.HospitalPatient.create(patient=patient, site=site, mrn='9999996')

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) is None


def test_create_patient() -> None:
    """A new patient can be created."""
    patient = utils.create_patient(
        first_name='Hans',
        last_name='Wurst',
        date_of_birth=date(1990, 10, 23),
        sex=SexType.MALE,
        ramq='',
        mrns=[],
    )

    assert patient.first_name == 'Hans'
    assert patient.last_name == 'Wurst'
    assert patient.date_of_birth == date(1990, 10, 23)
    assert patient.sex == SexType.MALE
    assert patient.ramq == ''
    assert HospitalPatient.objects.count() == 0


def test_create_patient_ramq() -> None:
    """A new patient can be created with a RAMQ."""
    patient = utils.create_patient(
        first_name='Hans',
        last_name='Wurst',
        date_of_birth=date(1990, 10, 23),
        sex=SexType.MALE,
        ramq='WURH90102399',
        mrns=[],
    )

    assert patient.ramq == 'WURH90102399'


def test_create_patient_hospitalpatients() -> None:
    """A new patient can be created with associated hospital patient instances."""
    site1 = Site.create()
    site2 = Site.create()
    patient = utils.create_patient(
        first_name='Hans',
        last_name='Wurst',
        date_of_birth=date(1990, 10, 23),
        sex=SexType.MALE,
        ramq='WURH90102399',
        mrns=[
            (site1, '9999991', True),
            (site2, '9999991', False),
        ],
    )

    assert HospitalPatient.objects.count() == 2
    hospital_patient1 = patient.hospital_patients.all()[0]
    hospital_patient2 = patient.hospital_patients.all()[1]

    assert hospital_patient1.site == site1
    assert hospital_patient1.mrn == '9999991'
    assert hospital_patient1.is_active

    assert hospital_patient2.site == site2
    assert hospital_patient2.mrn == '9999991'
    assert not hospital_patient2.is_active


def test_create_patient_hospitalpatients_error() -> None:
    """A new patient is created even though an error occurs when creating associated hospital patient instances."""
    site = Site.create()

    # keep the asserts within the context manager
    # the alternative is enabling transactions
    # this can cause issues since it flushes the database and loses the default relationship types
    with pytest.raises(IntegrityError):  # noqa: PT012
        utils.create_patient(
            first_name='Hans',
            last_name='Wurst',
            date_of_birth=date(1990, 10, 23),
            sex=SexType.MALE,
            ramq='WURH90102399',
            mrns=[
                (site, '9999991', True),
                (site, '9999992', False),
            ],
        )

        assert Patient.objects.count() == 1
        assert HospitalPatient.objects.count() == 0


def test_create_caregiver_profile() -> None:
    """A new caregiver profile and caregiver can be created."""
    caregiver_profile = utils.create_caregiver_profile('Hans', 'Wurst')

    caregiver_profile.full_clean()
    assert caregiver_profile.legacy_id is None

    caregiver = caregiver_profile.user
    caregiver.full_clean()

    assert caregiver.first_name == 'Hans'
    assert caregiver.last_name == 'Wurst'
    assert not caregiver.is_active
    assert not caregiver.has_usable_password()
    assert caregiver.username != ''
    assert len(caregiver.username) == utils.RANDOM_USERNAME_LENGTH


def test_create_caregiver_profile_multiple() -> None:
    """Ensure that multiple caregiver profiles can be created."""
    caregiver_profile = utils.create_caregiver_profile('Hans', 'Wurst')
    caregiver_profile2 = utils.create_caregiver_profile('Hans', 'Wurst')

    assert caregiver_profile.user.username != caregiver_profile2.user.username


def test_create_relationship() -> None:
    """A new confirmed relationship is created for a self relationship."""
    patient = patient_factories.Patient.create()
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()
    end_date = Relationship.calculate_end_date(
        patient.date_of_birth,
        self_type,
    )

    relationship = utils.create_relationship(
        patient,
        caregiver_profile,
        self_type,
        RelationshipStatus.CONFIRMED,
    )

    assert relationship.patient == patient
    assert relationship.caregiver == caregiver_profile
    assert relationship.type == self_type
    assert relationship.status == RelationshipStatus.CONFIRMED
    assert relationship.end_date == end_date


def test_create_relationship_no_defaults() -> None:
    """A new relationship can be created with specific values provided as arguments."""
    patient = patient_factories.Patient.create()
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()

    relationship = utils.create_relationship(
        patient,
        caregiver_profile,
        self_type,
        RelationshipStatus.CONFIRMED,
        date(2000, 2, 2),
        date(2000, 1, 2),
    )

    assert relationship.request_date == date(2000, 2, 2)
    assert relationship.start_date == date(2000, 1, 2)


def test_create_relationship_defaults() -> None:
    """A new relationship can be created with default values for unprovided arguments."""
    patient = patient_factories.Patient.create()
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()

    relationship = utils.create_relationship(
        patient,
        caregiver_profile,
        self_type,
        RelationshipStatus.CONFIRMED,
    )

    assert relationship.request_date == timezone.now().date()
    assert relationship.start_date == patient.date_of_birth


def test_create_registration_code(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """A new registration code can be created with a random code."""
    # mock the current time to a fixed value
    current_time = datetime(2022, 6, 2, 2, 0, tzinfo=dt.timezone.utc)
    mocker.patch.object(timezone, 'now', return_value=current_time)
    relationship = patient_factories.Relationship.create()
    settings.INSTITUTION_CODE = 'XY'

    registration_code = utils.create_registration_code(relationship)

    assert registration_code.relationship == relationship
    assert registration_code.code.startswith('XY')
    assert registration_code.created_at == current_time
    assert registration_code.status == caregiver_models.RegistrationCodeStatus.NEW


def test_initialize_new_opal_patient_orms_success(mocker: MockerFixture) -> None:
    """An info message is logged when the call to ORMS to initialize a patient succeeds."""
    RequestMockerTest.mock_requests_post(mocker, {'status': 'Success'})
    mock_error_logger = mocker.patch('logging.Logger.info')

    rvh_site: hospital_models.Site = Site.create(acronym='RVH')
    LegacyHospitalIdentifierType.create(code='RVH')
    mrn_list = [(rvh_site, '9999993', True)]
    patient = patient_factories.Patient.create()
    patient_uuid = uuid.uuid4()
    utils.initialize_new_opal_patient(patient, mrn_list, patient_uuid, None)

    mock_error_logger.assert_any_call(
        f'Successfully initialized patient via ORMS; patient_uuid = {patient_uuid}',
    )


@pytest.mark.usefixtures('set_orms_disabled')
def test_initialize_new_opal_patient_orms_success_disabled(mocker: MockerFixture) -> None:
    """An info message is logged when the call to ORMS is not executed because it is disabled."""
    RequestMockerTest.mock_requests_post(mocker, {'status': 'Success'})
    mock_logger = mocker.patch('logging.Logger.info')

    rvh_site: hospital_models.Site = Site.create(acronym='RVH')
    LegacyHospitalIdentifierType.create(code='RVH')
    mrn_list = [(rvh_site, '9999993', True)]
    patient = patient_factories.Patient.create()
    patient_uuid = uuid.uuid4()
    utils.initialize_new_opal_patient(patient, mrn_list, patient_uuid, None)
    mock_logger.assert_any_call(
        f'ORMS System not enabled, skipping notification of new patient; patient_uuid {patient_uuid}',
    )


def test_initialize_new_opal_patient_orms_error(mocker: MockerFixture) -> None:
    """An error is logged when the call to ORMS to initialize a patient fails."""
    RequestMockerTest.mock_requests_post(mocker, {'status': 'Error'})
    mock_error_logger = mocker.patch('logging.Logger.error')

    rvh_site: hospital_models.Site = Site.create(acronym='RVH')
    LegacyHospitalIdentifierType.create(code='RVH')
    mrn_list = [(rvh_site, '9999993', True)]
    patient = patient_factories.Patient.create()
    patient_uuid = uuid.uuid4()
    utils.initialize_new_opal_patient(patient, mrn_list, patient_uuid, None)

    mock_error_logger.assert_any_call('Failed to initialize patient via ORMS')


def test_initialize_new_opal_patient_source_system_success(mocker: MockerFixture) -> None:
    """An info message is logged when the call to the source system to initialize a patient succeeds."""
    RequestMockerTest.mock_requests_post(mocker, {})
    mock_error_logger = mocker.patch('logging.Logger.info')

    rvh_site: hospital_models.Site = Site.create(acronym='RVH')
    LegacyHospitalIdentifierType.create(code='RVH')
    mrn_list = [(rvh_site, '9999993', True)]
    patient = patient_factories.Patient.create()
    patient_uuid = uuid.uuid4()
    utils.initialize_new_opal_patient(patient, mrn_list, patient_uuid, None)

    mock_error_logger.assert_any_call(
        f'Successfully initialized patient via the source system; patient_uuid = {patient_uuid}',
    )


def test_initialize_new_opal_patient_source_system_error(mocker: MockerFixture, set_orms_disabled: None) -> None:
    """An error is logged when the call to the source system to initialize a patient fails."""
    mocker.patch(
        'requests.post',
        return_value=_MockResponse(HTTPStatus.BAD_REQUEST, {'status': HTTPStatus.BAD_REQUEST, 'message': 'error'}),
    )
    log_exception = mocker.spy(logging.Logger, 'exception')

    rvh_site: hospital_models.Site = Site.create(acronym='RVH')
    LegacyHospitalIdentifierType.create(code='RVH')
    mrn_list = [(rvh_site, '9999993', True)]
    patient = patient_factories.Patient.create()
    patient_uuid = uuid.uuid4()
    utils.initialize_new_opal_patient(patient, mrn_list, patient_uuid, None)

    log_exception.assert_called_once()
    message = log_exception.call_args_list[0].args[1]
    assert 'Failed to initialize patient via the source system' in message


def test_create_access_request_existing() -> None:
    """A new self relationship is created for an existing patient and caregiver."""
    patient = patient_factories.Patient.create()
    legacy_user = LegacyUser.create(usertype=LegacyUserType.CAREGIVER)
    caregiver_profile = CaregiverProfile.create(legacy_id=legacy_user.usersernum)
    self_type = RelationshipType.objects.self_type()

    relationship, registration_code = utils.create_access_request(
        patient,
        caregiver_profile,
        self_type,
    )
    legacy_user.refresh_from_db()

    assert registration_code is None
    assert relationship.patient == patient
    assert relationship.caregiver == caregiver_profile
    assert relationship.type == self_type
    assert relationship.status == RelationshipStatus.CONFIRMED
    assert relationship.request_date == timezone.now().date()
    assert relationship.start_date == patient.date_of_birth
    assert relationship.end_date is None
    assert legacy_user.usertype == LegacyUserType.PATIENT


def test_create_access_request_non_self() -> None:
    """A new relationship is created for a Parent/Guardian relationship."""
    patient = patient_factories.Patient.create(date_of_birth=date(2003, 3, 27))
    caregiver_profile = CaregiverProfile.create()
    parent_type = RelationshipType.objects.parent_guardian()

    relationship, registration_code = utils.create_access_request(
        patient,
        caregiver_profile,
        parent_type,
    )

    assert registration_code is None
    assert relationship.type == parent_type
    assert relationship.status == RelationshipStatus.PENDING
    assert relationship.request_date == timezone.now().date()
    assert relationship.start_date == patient.date_of_birth
    assert relationship.end_date == date(2017, 3, 27)


def test_create_access_request_new_patient() -> None:
    """A new relationship and new patient are created."""
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()
    Institution.create()

    relationship, registration_code = utils.create_access_request(
        PATIENT_DATA,
        caregiver_profile,
        self_type,
    )

    assert registration_code is None
    patient = Patient.objects.get()

    assert relationship.patient == patient
    assert patient.first_name == 'Marge'
    assert patient.last_name == 'Simpson'
    assert patient.date_of_birth == date(1986, 10, 1)
    assert patient.sex == SexType.FEMALE
    assert patient.ramq == 'SIMM86600199'
    assert patient.date_of_death is None
    assert HospitalPatient.objects.count() == 0


def test_create_access_request_new_patient_mrns_missing_site() -> None:
    """Everything is rolled back in case of an error such as a missing site."""
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()

    patient_data = PatientSchema.model_copy(PATIENT_DATA)
    patient_data.mrns = [MRN_DATA_RVH, MRN_DATA_MGH]

    with pytest.raises(hospital_models.Site.DoesNotExist):
        utils.create_access_request(
            patient_data,
            caregiver_profile,
            self_type,
        )

    assert Patient.objects.count() == 0
    assert HospitalPatient.objects.count() == 0
    assert Relationship.objects.count() == 0


def test_create_access_request_new_patient_mrns(mocker: MockerFixture) -> None:
    """A new relationship and patient are created along with associated hospital patient instances."""
    RequestMockerTest.mock_requests_post(mocker, {})
    Site.create(acronym='RVH')
    Site.create(acronym='MGH')
    LegacyHospitalIdentifierType.create(code='RVH')
    LegacyHospitalIdentifierType.create(code='MGH')
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()

    patient_data = PatientSchema.model_copy(PATIENT_DATA)
    patient_data.mrns = [MRN_DATA_RVH, MRN_DATA_MGH]

    relationship, _ = utils.create_access_request(
        patient_data,
        caregiver_profile,
        self_type,
    )

    assert Patient.objects.count() == 1
    patient = relationship.patient

    hospital_patients = HospitalPatient.objects.filter(patient=patient)
    assert hospital_patients.count() == 2

    hospital_patient_rvh = hospital_patients[0]
    assert hospital_patient_rvh.mrn == '9999993'
    assert hospital_patient_rvh.is_active

    hospital_patient_mgh = hospital_patients[1]
    assert hospital_patient_mgh.mrn == '9999996'
    assert not hospital_patient_mgh.is_active


def test_create_access_request_new_caregiver() -> None:
    """A new relationship and new caregiver are created."""
    patient = patient_factories.Patient.create()
    self_type = RelationshipType.objects.self_type()

    relationship, registration_code = utils.create_access_request(
        patient,
        ('Marge', 'Simpson'),
        self_type,
    )

    assert registration_code is not None
    assert caregiver_models.CaregiverProfile.objects.count() == 1
    assert user_models.Caregiver.objects.count() == 1

    caregiver_profile = caregiver_models.CaregiverProfile.objects.get()
    caregiver = caregiver_profile.user
    assert relationship.caregiver == caregiver_profile

    assert caregiver.first_name == 'Marge'
    assert caregiver.last_name == 'Simpson'
    assert not caregiver.is_active
    assert not caregiver.has_usable_password()


def test_create_access_request_new_caregiver_registration_code(settings: SettingsWrapper) -> None:
    """A registration code is created for a new caregiver."""
    patient = patient_factories.Patient.create()
    self_type = RelationshipType.objects.self_type()

    relationship, registration_code = utils.create_access_request(
        patient,
        ('Marge', 'Simpson'),
        self_type,
    )

    assert caregiver_models.RegistrationCode.objects.count() == 1

    assert registration_code is not None
    assert registration_code.relationship == relationship
    assert registration_code.code.startswith(settings.INSTITUTION_CODE)


def test_create_access_request_self_relationship_already_exists() -> None:
    """Creating an access request is atomic."""
    self_type = RelationshipType.objects.self_type()
    existing_relationship = patient_factories.Relationship.create(type=self_type)

    with pytest.raises(ValidationError, match='The patient already has a self-relationship'):
        utils.create_access_request(
            existing_relationship.patient,
            existing_relationship.caregiver,
            self_type,
        )

    assert caregiver_models.CaregiverProfile.objects.count() == 1
    assert user_models.Caregiver.objects.count() == 1
    assert Relationship.objects.count() == 1
    assert Patient.objects.count() == 1


def test_create_access_request_new_patient_caregiver() -> None:
    """A new relationship, patient, caregiver and registration code are created."""
    self_type = RelationshipType.objects.self_type()
    Institution.create()

    _relationship, registration_code = utils.create_access_request(
        PATIENT_DATA,
        ('Marge', 'Simpson'),
        self_type,
    )

    assert registration_code is not None
    assert caregiver_models.CaregiverProfile.objects.count() == 1
    assert user_models.Caregiver.objects.count() == 1
    assert Relationship.objects.count() == 1
    assert Patient.objects.count() == 1


def test_create_access_request_missing_legacy_id() -> None:
    """An error occurs if an existing user registers as self but is missing their legacy_id."""
    caregiver_profile = CaregiverProfile.create(legacy_id=None)
    patient = patient_factories.Patient.create()
    self_type = RelationshipType.objects.self_type()

    with assertRaisesMessage(ValueError, 'Legacy ID is missing'):
        utils.create_access_request(
            patient,
            caregiver_profile,
            self_type,
        )


def test_create_access_request_pediatric_patient_delay_value(mocker: MockerFixture, set_orms_disabled: None) -> None:
    """A new pediatric patient gets lab delay values according to the institution settings."""
    RequestMockerTest.mock_requests_post(mocker, {})
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()
    institution = Institution.create(non_interpretable_lab_result_delay=3, interpretable_lab_result_delay=5)

    patient_data = PatientSchema.model_copy(PATIENT_DATA)
    patient_data.date_of_birth = datetime(2008, 10, 23, tzinfo=timezone.get_current_timezone())

    relationship, registration_code = utils.create_access_request(
        patient_data,
        caregiver_profile,
        self_type,
    )

    assert registration_code is None
    patient = relationship.patient

    assert patient.age < institution.adulthood_age
    assert patient.non_interpretable_lab_result_delay == institution.non_interpretable_lab_result_delay
    assert patient.interpretable_lab_result_delay == institution.interpretable_lab_result_delay


@pytest.mark.parametrize('role_type', PREDEFINED_ROLE_TYPES)
def test_create_access_request_legacy_data_self(mocker: MockerFixture, role_type: RoleType) -> None:
    """Legacy data is saved when requesting access to a new patient for an existing caregiver (as self)."""
    RequestMockerTest.mock_requests_post(mocker, {})
    Site.create(acronym='RVH')
    Site.create(acronym='MGH')
    LegacyHospitalIdentifierType.create(code='RVH')
    LegacyHospitalIdentifierType.create(code='MGH')
    caregiver_profile = CaregiverProfile.create()
    relationship_type = RelationshipType.objects.get(role_type=role_type)
    patient_data = PatientSchema.model_copy(PATIENT_DATA)
    patient_data.mrns = [MRN_DATA_RVH, MRN_DATA_MGH]

    utils.create_access_request(
        patient_data,
        caregiver_profile,
        relationship_type,
    )

    legacy_patient = LegacyPatient.objects.get(ramq=patient_data.health_insurance_number)
    patient = Patient.objects.get(ramq=patient_data.health_insurance_number)
    legacy_mrn_list = LegacyPatientHospitalIdentifier.objects.filter(patient=legacy_patient)

    assert patient.legacy_id == legacy_patient.patientsernum
    assert legacy_patient.first_name == patient_data.first_name
    assert legacy_patient.last_name == patient_data.last_name
    assert legacy_patient.date_of_birth.strftime('%Y-%m-%d') == '1986-10-01'
    assert legacy_patient.sex == 'Female'
    assert legacy_patient.death_date is None
    assert legacy_patient.access_level == '3'

    # Two categories of parametrized test cases: self vs non-self
    if relationship_type.is_self:
        assert legacy_patient.email == caregiver_profile.user.email
        assert legacy_patient.language == caregiver_profile.user.language.upper()
    else:
        assert legacy_patient.email == ''
        assert legacy_patient.language == 'FR'

    assert legacy_mrn_list.filter(mrn='9999993', hospital__code='RVH', is_active=True).count() == 1
    assert legacy_mrn_list.filter(mrn='9999996', hospital__code='MGH', is_active=False).count() == 1

    assert LegacyPatientControl.objects.filter(patient=legacy_patient).count() == 1


def test_create_access_request_new_patient_and_databank_consent(
    databank_consent_questionnaire_data: tuple[qdb_LegacyQuestionnaire, LegacyEducationalMaterialControl],
) -> None:
    """A new relationship and new patient with databank consent records are created."""
    consent_form = databank_consent_questionnaire_data[0]
    info_sheet = databank_consent_questionnaire_data[1]
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()
    Institution.create()

    relationship, registration_code = utils.create_access_request(
        PATIENT_DATA,
        caregiver_profile,
        self_type,
    )

    assert registration_code is None
    patient = Patient.objects.get()

    assert relationship.patient == patient
    assert patient.first_name == 'Marge'
    assert patient.last_name == 'Simpson'
    assert patient.date_of_birth == date(1986, 10, 1)
    assert patient.sex == SexType.FEMALE
    assert patient.ramq == 'SIMM86600199'
    assert patient.date_of_death is None
    assert HospitalPatient.objects.count() == 0
    assert patient.legacy_id is not None

    # Search for the expected databank records
    qdb_patient = LegacyQuestionnairePatient.objects.get(
        external_id=patient.legacy_id,
    )
    inserted_answer_questionnaire = LegacyAnswerQuestionnaire.objects.get(
        questionnaire_id=consent_form.id,
        patient_id=qdb_patient.id,
    )
    inserted_sheet = LegacyEducationalMaterial.objects.get(
        educationalmaterialcontrolsernum=info_sheet,
        patientsernum=patient.legacy_id,
    )
    inserted_questionnaire = LegacyQuestionnaire.objects.get(
        patientsernum=patient.legacy_id,
        patient_questionnaire_db_ser_num=inserted_answer_questionnaire.id,
    )
    assert inserted_questionnaire.completedflag == 0
    assert inserted_questionnaire.patientsernum.patientsernum == patient.legacy_id
    assert inserted_questionnaire.patient_questionnaire_db_ser_num == inserted_answer_questionnaire.id

    assert inserted_sheet.readstatus == 0
    assert inserted_sheet.patientsernum.patientsernum == patient.legacy_id
    assert inserted_sheet.educationalmaterialcontrolsernum == info_sheet

    assert inserted_answer_questionnaire.status == 0
    assert inserted_answer_questionnaire.patient_id == qdb_patient.id
    assert inserted_answer_questionnaire.questionnaire_id == consent_form.id


@pytest.mark.usefixtures('set_databank_disabled')
def test_create_access_request_new_patient_databank_disabled(
    databank_consent_questionnaire_data: tuple[qdb_LegacyQuestionnaire, LegacyEducationalMaterialControl],
) -> None:
    """Ensure the databank consent form is not created if databank is disabled."""
    caregiver_profile = CaregiverProfile.create()
    self_type = RelationshipType.objects.self_type()
    Institution.create()
    info_sheet = databank_consent_questionnaire_data[1]
    relationship, registration_code = utils.create_access_request(
        PATIENT_DATA,
        caregiver_profile,
        self_type,
    )

    assert registration_code is None
    patient = Patient.objects.get()

    assert relationship.patient == patient
    assert patient.first_name == 'Marge'
    assert patient.last_name == 'Simpson'
    assert patient.date_of_birth == date(1986, 10, 1)
    assert patient.sex == SexType.FEMALE
    assert patient.ramq == 'SIMM86600199'
    assert patient.date_of_death is None
    assert HospitalPatient.objects.count() == 0
    assert patient.legacy_id is not None

    # Ensure records are not created
    message = 'LegacyQuestionnairePatient matching query does not exist.'
    with assertRaisesMessage(ObjectDoesNotExist, message):
        LegacyQuestionnairePatient.objects.get(
            external_id=patient.legacy_id,
        )
    message = 'LegacyEducationalMaterial matching query does not exist.'
    with assertRaisesMessage(ObjectDoesNotExist, message):
        LegacyEducationalMaterial.objects.get(
            educationalmaterialcontrolsernum=info_sheet,
            patientsernum=patient.legacy_id,
        )
    # We cant search for the specific answer questionnaire instance without the qdb_patient instance, so check all
    answer_questionnaires = LegacyAnswerQuestionnaire.objects.all()
    for qst in answer_questionnaires:
        assert qst.created_by != 'DJANGO_AUTO_CREATE_DATABANK_CONSENT'
