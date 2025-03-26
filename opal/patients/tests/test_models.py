import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.caregivers.models import CaregiverProfile
from opal.users import factories as user_factories

from .. import constants, factories
from ..models import HospitalPatient, RelationshipStatus, RelationshipType

pytestmark = pytest.mark.django_db


def test_relationshiptype_str() -> None:
    """Ensure the `__str__` method is defined for the `RelationshipType` model."""
    relationship_type = RelationshipType(name='Test User Patient Relationship Type')
    assert str(relationship_type) == 'Test User Patient Relationship Type'


def test_relationshiptype_duplicate_names() -> None:
    """Ensure that the relationship type name is unique."""
    factories.RelationshipType(name='Self')

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'Self' for key 'name'"):  # type: ignore[arg-type]
        factories.RelationshipType(name='Self')


def test_relationshiptype_min_age_lowerbound() -> None:
    """Ensure the minimum age lower bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.start_age = constants.RELATIONSHIP_MIN_AGE - 1

    message = 'Ensure this value is greater than or equal to {0}.'.format(constants.RELATIONSHIP_MIN_AGE)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.start_age = constants.RELATIONSHIP_MIN_AGE
    relationship_type.full_clean()


def test_relationshiptype_min_age_upperbound() -> None:
    """Ensure the minimum age upper bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.start_age = constants.RELATIONSHIP_MAX_AGE

    message = 'Ensure this value is less than or equal to {0}.'.format(constants.RELATIONSHIP_MAX_AGE - 1)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.start_age = constants.RELATIONSHIP_MAX_AGE - 1
    relationship_type.full_clean()


def test_relationshiptype_max_age_lowerbound() -> None:
    """Ensure the maximum age lower bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.end_age = constants.RELATIONSHIP_MIN_AGE

    message = 'Ensure this value is greater than or equal to {0}.'.format(constants.RELATIONSHIP_MIN_AGE + 1)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.end_age = constants.RELATIONSHIP_MIN_AGE + 1
    relationship_type.full_clean()


def test_relationshiptype_max_age_upperbound() -> None:
    """Ensure the maximum age upper bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.end_age = constants.RELATIONSHIP_MAX_AGE + 1

    message = 'Ensure this value is less than or equal to {0}.'.format(constants.RELATIONSHIP_MAX_AGE)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.end_age = constants.RELATIONSHIP_MAX_AGE
    relationship_type.full_clean()


def test_patient_str() -> None:
    """Ensure the `__str__` method is defined for the `Patient` model."""
    patient = factories.Patient(first_name='First Name', last_name='Last Name')
    assert str(patient) == 'First Name Last Name'


def test_patient_factory() -> None:
    """Ensure the Patient factory is building properly."""
    patient = factories.Patient()
    patient.full_clean()


def test_relationship_str() -> None:
    """Ensure the `__str__` method is defined for the `Relationship` model."""
    patient = factories.Patient(first_name='Kobe', last_name='Briant')

    caregiver = user_factories.Caregiver(first_name='John', last_name='Wayne')
    profile = CaregiverProfile()
    profile.user = caregiver

    relationshiptype = factories.RelationshipType(name='caregiver', name_fr='Proche aidant')

    relationship = factories.Relationship()
    relationship.patient = patient
    relationship.caregiver = profile
    relationship.type = relationshiptype

    assert str(relationship) == 'Kobe Briant <--> John Wayne [caregiver]'


def test_relationship_factory() -> None:
    """Ensure the Relationship factory is building properly."""
    relationship = factories.Relationship()
    relationship.full_clean()


def test_relationship_default_status() -> None:
    """Relationship has the default relationship status set."""
    relationship = factories.Relationship()

    assert relationship.status == RelationshipStatus.PENDING


def test_relationship_clean_no_end_date() -> None:
    """Ensure that the relationship with start date but without end date."""
    relationship = factories.Relationship(start_date='2022-05-04', end_date=None)

    relationship.clean()


def test_relationship_clean_valid_dates() -> None:
    """Ensure that the date is valid if start date is earlier than end date."""
    relationship = factories.Relationship(start_date='2022-05-01', end_date='2022-05-04')

    relationship.clean()


def test_relationship_clean_invalid_dates() -> None:
    """Ensure that the date is invalid if start date is later than end date."""
    relationship = factories.Relationship()
    relationship.start_date = datetime.date(2022, 5, 8)
    relationship.end_date = datetime.date(2022, 5, 4)

    expected_message = 'Start date should be earlier than end date.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        relationship.clean()


def test_relationship_invalid_dates_constraint() -> None:
    """Ensure that the date cannot be saved if start date is later than end date."""
    relationship = factories.Relationship()
    relationship.start_date = datetime.date(2022, 5, 8)
    relationship.end_date = datetime.date(2022, 5, 4)

    constraint_name = 'patients_relationship_date_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        relationship.save()


def test_relationship_status_constraint() -> None:
    """Error happens when assigning an invalid Relationship status."""
    relationship = factories.Relationship()
    relationship.status = 'INV'

    constraint_name = 'patients_relationship_status_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):  # type: ignore[arg-type]
        relationship.save()


def test_hospitalpatient_factory() -> None:
    """Ensure the Patient factory is building properly."""
    hospital_patient = factories.HospitalPatient()
    hospital_patient.full_clean()


def test_hospitalpatient_one_patient_one_site() -> None:
    """Ensure the `__str__` method is defined for the `HospitalPatient` model."""
    hospitalpatient = factories.HospitalPatient()
    hospitalpatient.site = factories.Site(name="Montreal Children's Hospital")
    assert str(hospitalpatient) == 'Patient First Name Patient Last Name (MON: 9999996)'


def test_hospitalpatient_one_patient_many_sites() -> None:
    """Test one patient has many hospital_patients."""
    patient = factories.Patient(first_name='aaa', last_name='bbb')
    site1 = factories.Site(name="Montreal Children's Hospital")
    site2 = factories.Site(name='Royal Victoria Hospital')

    HospitalPatient.objects.create(patient=patient, site=site1, mrn='9999996')
    HospitalPatient.objects.create(patient=patient, site=site2, mrn='9999996')
    hospitalpatients = HospitalPatient.objects.all()
    assert len(hospitalpatients) == 2

    with assertRaisesMessage(IntegrityError, 'Duplicate entry'):  # type: ignore[arg-type]
        HospitalPatient.objects.create(patient=patient, site=site1, mrn='9999996')
