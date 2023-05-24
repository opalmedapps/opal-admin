"""App patient utils test functions."""
import datetime as dt
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

import pytest
from pytest_django.asserts import assertRaisesMessage
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from opal.caregivers import models as caregiver_models
from opal.caregivers.factories import CaregiverProfile, RegistrationCode
from opal.hospital_settings.factories import Site
from opal.patients import factories as patient_factories
from opal.patients.models import (
    HospitalPatient,
    Patient,
    Relationship,
    RelationshipStatus,
    RelationshipType,
    RoleType,
    SexType,
)
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData
from opal.users.factories import User

from .. import utils

pytestmark = pytest.mark.django_db


CUSTOMIZED_OIE_PATIENT_DATA = OIEPatientData(
    date_of_birth=date.fromisoformat('1954-05-09'),
    first_name='Marge',
    last_name='Simpson',
    sex='F',
    alias='',
    deceased=False,
    death_date_time=datetime.strptime('2054-05-09 09:20:30', '%Y-%m-%d %H:%M:%S'),
    ramq='MARG99991313',
    ramq_expiration=datetime.strptime('2024-01-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
    mrns=[
        OIEMRNData(
            site='MGH',
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


@pytest.mark.parametrize(('first_name', 'last_name', 'date_of_birth', 'sex', 'ramq'), [
    # one-digit month
    ('Bart', 'Wayne', date(2013, 2, 23), SexType.MALE, 'WAYB13022399'),
    # one-digit day (and female)
    ('Marge', 'Simpson', date(1986, 10, 1), SexType.FEMALE, 'SIMM86600199'),
])
def test_build_ramq(first_name: str, last_name: str, date_of_birth: date, sex: SexType, ramq: str) -> None:
    """The RAMQ is derived correctly."""
    assert utils.build_ramq(first_name, last_name, date_of_birth, sex) == ramq


def test_update_registration_code_status_success() -> None:
    """Test get registration code and update its status success."""
    registration_code = RegistrationCode(status=caregiver_models.RegistrationCodeStatus.NEW)
    utils.update_registration_code_status(registration_code)
    registration_code.refresh_from_db()
    assert registration_code.status == caregiver_models.RegistrationCodeStatus.REGISTERED


def test_update_patient_legacy_id_valid() -> None:
    """Test update patient legacy id with valid value."""
    patient = patient_factories.Patient()
    legacy_id = patient.legacy_id + 1
    utils.update_patient_legacy_id(patient, legacy_id)
    patient.refresh_from_db()
    assert patient.legacy_id == legacy_id


def test_update_patient_legacy_id_invalid() -> None:
    """Test update patient legacy id with invalid value."""
    patient = patient_factories.Patient()
    legacy_id = 0
    expected_message = "'legacy_id': ['Ensure this value is greater than or equal to 1.']"
    with assertRaisesMessage(
        ValidationError,
        expected_message,
    ):
        utils.update_patient_legacy_id(patient, legacy_id)


def test_update_caregiver_success() -> None:
    """Test update caregiver information success."""
    phone_number1 = '+15141112222'
    phone_number2 = '+15141112223'
    language1 = 'en'
    language2 = 'fr'
    user = User(phone_number=phone_number1, language=language1)
    info: dict = {
        'user': {
            'language': language2,
            'phone_number': phone_number2,
        },
    }
    utils.update_caregiver(user, info)
    user.refresh_from_db()
    assert user.language == language2
    assert user.phone_number == phone_number2


def test_update_caregiver_failure() -> None:
    """Test update caregiver information failure."""
    phone_number1 = '+15141112222'
    phone_number2 = '11111112223'
    language1 = 'en'
    language2 = 'fr'
    user = User(phone_number=phone_number1, language=language1)
    info: dict = {
        'user': {
            'language': language2,
            'phone_number': phone_number2,
        },
    }
    expected_message = "{'phone_number': ['Enter a valid value.']}"
    with assertRaisesMessage(
        ValidationError,
        expected_message,
    ):
        utils.update_caregiver(user, info)


def test_insert_security_answers_success() -> None:
    """Test insert security answers success."""
    caregiver = CaregiverProfile()
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
    caregiver = CaregiverProfile()
    security_answers = [
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
    patient = patient_factories.Patient()

    valid_types = list(utils.valid_relationship_types(patient).values_list('role_type', flat=True))

    assert RoleType.SELF in valid_types
    assert RoleType.MANDATARY in valid_types


def test_valid_relationship_types_not_contain_self_role_type() -> None:
    """Get the queryset of valid relationship types doesn't contain self role type."""
    patient = patient_factories.Patient()
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

    patient = patient_factories.Patient(ramq=ramq)

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) == patient


def test_get_patient_by_ramq_in_failed() -> None:
    """Get the patient instance by RAMQ in failed."""
    ramq = 'MARG99991313'
    mrn = '9999993'
    site_code = 'MGH'
    patient_factories.Patient(ramq='')

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) is None


def test_get_patient_by_mrn_in_success() -> None:
    """Get the patient instance by MRN and site code in success."""
    ramq = ''
    mrn = '9999993'
    site_code = 'MGH'
    patient = patient_factories.Patient()
    site = Site(code=site_code)
    patient_factories.HospitalPatient(patient=patient, site=site, mrn=mrn)

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) == patient


def test_get_patient_by_mrn_in_failed() -> None:
    """Get the patient instance by MRN and site code in failed."""
    ramq = ''
    mrn = '9999993'
    site_code = 'MGH'
    patient = patient_factories.Patient()
    site = Site(code=site_code)
    patient_factories.HospitalPatient(patient=patient, site=site, mrn='9999996')

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) is None


def test_create_patient() -> None:
    """A new patient can be created."""
    patient = utils.create_patient(
        first_name='Hans',
        last_name='Wurst',
        date_of_birth=date(1990, 10, 23),
        sex=SexType.MALE,
        ramq=None,
        mrns=[],
    )

    assert patient.first_name == 'Hans'
    assert patient.last_name == 'Wurst'
    assert patient.date_of_birth == date(1990, 10, 23)
    assert patient.sex == SexType.MALE
    assert patient.ramq is None
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
    site1 = Site()
    site2 = Site()
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


@pytest.mark.django_db(transaction=True)
def test_create_patient_hospitalpatients_error() -> None:
    """A new patient can be created with associated hospital patient instances."""
    site = Site()

    with pytest.raises(IntegrityError):
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
    caregiver.full_clean(exclude=['password', 'username'])

    assert caregiver.first_name == 'Hans'
    assert caregiver.last_name == 'Wurst'
    assert caregiver.is_active is False
    assert caregiver.username == ''


def test_create_relationship() -> None:
    """A new relationship can be created."""
    patient = patient_factories.Patient()
    caregiver_profile = CaregiverProfile()
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
    patient = patient_factories.Patient()
    caregiver_profile = CaregiverProfile()
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
    patient = patient_factories.Patient()
    caregiver_profile = CaregiverProfile()
    self_type = RelationshipType.objects.self_type()

    relationship = utils.create_relationship(
        patient,
        caregiver_profile,
        self_type,
        RelationshipStatus.CONFIRMED,
    )

    assert relationship.request_date == date.today()
    assert relationship.start_date == patient.date_of_birth


def test_create_registration_code(mocker: MockerFixture, settings: SettingsWrapper) -> None:
    """A new registration code can be created with a random code."""
    # mock the current time to a fixed value
    current_time = datetime(2022, 6, 2, 2, 0, tzinfo=dt.timezone.utc)
    mocker.patch.object(timezone, 'now', return_value=current_time)
    relationship = patient_factories.Relationship()
    settings.INSTITUTION_CODE = 'XY'

    registration_code = utils.create_registration_code(relationship)

    assert registration_code.relationship == relationship
    assert registration_code.code.startswith('XY')
    assert registration_code.created_at == current_time
    assert registration_code.status == caregiver_models.RegistrationCodeStatus.NEW
