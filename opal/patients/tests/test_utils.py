"""App patient utils test functions."""
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.caregivers import models as caregiver_models
from opal.caregivers.factories import CaregiverProfile, RegistrationCode
from opal.hospital_settings.factories import Site
from opal.patients.factories import HospitalPatient, Patient, Relationship
from opal.patients.models import RelationshipType, RoleType, SexType
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
    patient = Patient()
    legacy_id = patient.legacy_id + 1
    utils.update_patient_legacy_id(patient, legacy_id)
    patient.refresh_from_db()
    assert patient.legacy_id == legacy_id


def test_update_patient_legacy_id_invalid() -> None:
    """Test update patient legacy id with invalid value."""
    patient = Patient()
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
    patient = Patient()

    valid_types = list(utils.valid_relationship_types(patient).values_list('role_type', flat=True))

    assert RoleType.SELF in valid_types
    assert RoleType.MANDATARY in valid_types


def test_valid_relationship_of_self_contain_self_role_type() -> None:
    """Get the queryset of valid relationship types when instance being updated is of self type."""
    patient = Patient()

    valid_types = list(
        utils.valid_relationship_types(
            patient,
        ).values_list('role_type', flat=True),
    )

    assert RoleType.SELF in valid_types
    assert RoleType.MANDATARY in valid_types


def test_valid_relationship_contain_role_type_being_updated() -> None:
    """Ensure to include type being updated in the valid types list."""
    patient = Patient()

    valid_types = list(
        utils.valid_relationship_types(
            patient,
        ).values_list('role_type', flat=True),
    )

    assert RoleType.SELF in valid_types
    assert RoleType.MANDATARY in valid_types


def test_valid_relationship_types_not_contain_self_role_type() -> None:
    """Get the queryset of valid relationship types doesn't contain self role type."""
    patient = Patient()
    Relationship.create(
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

    patient = Patient(ramq=ramq)

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) == patient


def test_get_patient_by_ramq_in_failed() -> None:
    """Get the patient instance by RAMQ in failed."""
    ramq = 'MARG99991313'
    mrn = '9999993'
    site_code = 'MGH'
    Patient(ramq='')

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) is None


def test_get_patient_by_mrn_in_success() -> None:
    """Get the patient instance by MRN and site code in success."""
    ramq = ''
    mrn = '9999993'
    site_code = 'MGH'
    patient = Patient()
    site = Site(code=site_code)
    HospitalPatient(patient=patient, site=site, mrn=mrn)

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) == patient


def test_get_patient_by_mrn_in_failed() -> None:
    """Get the patient instance by MRN and site code in failed."""
    ramq = ''
    mrn = '9999993'
    site_code = 'MGH'
    patient = Patient()
    site = Site(code=site_code)
    HospitalPatient(patient=patient, site=site, mrn='9999996')

    assert utils.get_patient_by_ramq_or_mrn(ramq, mrn, site_code) is None
