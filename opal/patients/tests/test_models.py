import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.caregivers.models import CaregiverProfile
from opal.users import factories as user_factories

from .. import constants, factories
from ..models import HospitalPatient, Patient, RelationshipStatus, RelationshipType

pytestmark = pytest.mark.django_db


def test_relationshiptype_factory() -> None:
    """Ensure the RelationshipType factory is building properly."""
    relationship_type = factories.RelationshipType()
    relationship_type.full_clean()


def test_relationshiptype_factory_multiple() -> None:
    """Ensure the RelationshipType factory can build multiple default model instances."""
    relationship_type = factories.RelationshipType()
    relationship_type2 = factories.RelationshipType()

    assert relationship_type == relationship_type2


def test_relationshiptype_str() -> None:
    """Ensure the `__str__` method is defined for the `RelationshipType` model."""
    relationship_type = RelationshipType(name='Test User Patient Relationship Type')
    assert str(relationship_type) == 'Test User Patient Relationship Type'


def test_relationshiptype_duplicate_names() -> None:
    """Ensure that the relationship type name is unique."""
    factories.RelationshipType(name='Self')

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'Self' for key 'name'"):  # type: ignore[arg-type]
        relationship_type = factories.RelationshipType.build(name='Self')
        relationship_type.save()


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
    patient = Patient(first_name='First Name', last_name='Last Name')
    assert str(patient) == 'First Name Last Name'


def test_patient_factory() -> None:
    """Ensure the Patient factory is building properly."""
    patient = factories.Patient()
    patient.full_clean()


def test_patient_factory_multiple() -> None:
    """Ensure the Patient factory can build multiple default model instances."""
    patient = factories.Patient()
    patient2 = factories.Patient()

    assert patient == patient2


def test_patient_invalid_sex() -> None:
    """Ensure that a patient cannot be saved with an invalid sex type."""
    message = 'CONSTRAINT `patients_patient_sex_valid` failed'
    with assertRaisesMessage(IntegrityError, message):  # type: ignore[arg-type]
        factories.Patient(sex='I')


def test_patient_ramq_unique() -> None:
    """Ensure that the health insurance number is unique."""
    factories.Patient(ramq='TEST12345678')
    patient = factories.Patient(ramq='TEST21234567')

    message = "Duplicate entry 'TEST12345678' for key 'ramq'"

    with assertRaisesMessage(IntegrityError, message):  # type: ignore[arg-type]
        patient.ramq = 'TEST12345678'
        patient.save()


def test_patient_ramq_max() -> None:
    """Ensure the length of patient ramq is not greater than 12."""
    patient = factories.Patient()
    patient.ramq = 'ABCD5678901234'
    expected_message = '{0}, {1}'.format(
        "'ramq': ['Enter a valid RAMQ number consisting of 4 letters followed by 8 digits'",
        "'Ensure this value has at most 12 characters (it has 14).']",
    )
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        patient.clean_fields()


def test_patient_ramq_min() -> None:
    """Ensure the length of patient ramq is not less than 12."""
    patient = factories.Patient(ramq='ABCD56')
    expected_message = '{0}'.format(
        "'ramq': ['Ensure this value has at least 12 characters (it has 6).'",
    )
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        patient.clean_fields()


def test_patient_ramq_format() -> None:
    """Ensure the first 4 chars of patient ramq are alphabetic and last 8 chars are numeric."""
    patient = factories.Patient(ramq='ABC123456789')
    expected_message = '{0}'.format(
        "'ramq': ['Enter a valid RAMQ number consisting of 4 letters followed by 8 digits']",
    )
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        patient.clean_fields()


def test_patient_ramq_default_value() -> None:
    """Ensure patient ramq default value is NULL."""
    patient = Patient(
        date_of_birth='2022-09-02',
        sex='m',
    )
    patient.save()
    assert patient.ramq is None


def test_patient_legacy_id_unique() -> None:
    """Ensure that creating a second `Patient` with an existing `legacy_id` raises an `IntegrityError`."""
    factories.Patient(ramq=None, legacy_id=1)
    message = "Duplicate entry '1' for key"

    with assertRaisesMessage(IntegrityError, message):  # type: ignore[arg-type]
        factories.Patient(ramq='somevalue', legacy_id=1)


def test_patient_non_existing_legacy_id() -> None:
    """Ensure that creating a second `Patient` with a non-existing legacy_id does not raise a `ValidationError`."""
    factories.Patient(ramq=None, legacy_id=None)
    factories.Patient(ramq='somevalue', legacy_id=None)

    assert Patient.objects.count() == 2


def test_relationship_str() -> None:
    """Ensure the `__str__` method is defined for the `Relationship` model."""
    patient = factories.Patient(first_name='Kobe', last_name='Briant')

    caregiver = user_factories.Caregiver(first_name='John', last_name='Wayne')
    profile = CaregiverProfile(user=caregiver)

    relationship = factories.Relationship.build(patient=patient, caregiver=profile)

    assert str(relationship) == 'Kobe Briant <--> John Wayne [Self]'


def test_relationship_factory() -> None:
    """Ensure the Relationship factory is building properly."""
    relationship = factories.Relationship()
    relationship.full_clean()


def test_relationship_factory_multiple() -> None:
    """Ensure the Relationship factory can build multiple default model instances."""
    relationship = factories.Relationship()
    relationship2 = factories.Relationship()

    assert relationship != relationship2
    assert relationship.patient == relationship2.patient
    assert relationship.caregiver != relationship2.caregiver
    assert relationship.type == relationship2.type


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


def test_hospitalpatient_factory_multiple() -> None:
    """Ensure the Patient factory can build multiple default model instances."""
    hospital_patient = factories.HospitalPatient()
    hospital_patient2 = factories.HospitalPatient()

    assert hospital_patient != hospital_patient2
    assert hospital_patient.patient == hospital_patient2.patient
    assert hospital_patient.site != hospital_patient2.site


def test_hospitalpatient_str() -> None:
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


def test_hospitalpatient_many_patients_one_site() -> None:
    """Test many patients have the same site and mrn."""
    patient1 = factories.Patient(first_name='aaa', last_name='111')
    patient2 = factories.Patient(
        first_name='bbb',
        last_name='222',
    )
    site = factories.Site(name="Montreal Children's Hospital")

    HospitalPatient.objects.create(patient=patient1, site=site, mrn='9999996')

    with assertRaisesMessage(IntegrityError, 'Duplicate entry'):  # type: ignore[arg-type]
        HospitalPatient.objects.create(patient=patient2, site=site, mrn='9999996')


# tests for reason field constraints and validations
def test_relationship_no_reason_invalid_revoked() -> None:
    """Ensure that error is thrown when reason is empty and status is revoked."""
    relationship = factories.Relationship()
    relationship.reason = ''
    relationship.status = RelationshipStatus.REVOKED

    expected_message = 'Reason is mandatory when status is denied or revoked.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        relationship.clean()


def test_relationship_no_reason_invalid_denied() -> None:
    """Ensure that error is thrown when reason is empty and status is denied."""
    relationship = factories.Relationship()
    relationship.reason = ''
    relationship.status = RelationshipStatus.DENIED

    expected_message = 'Reason is mandatory when status is denied or revoked.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        relationship.clean()


def test_relationship_valid_reason_pass_denied() -> None:
    """Ensure that error is not thrown when reason field has content and status is denied."""
    relationship = factories.Relationship()
    relationship.status = RelationshipStatus.DENIED

    relationship.clean()


def test_relationship_valid_reason_pass_revoked() -> None:
    """Ensure that error is not thrown when reason field has content and status is revoked."""
    relationship = factories.Relationship()
    relationship.status = RelationshipStatus.REVOKED

    relationship.clean()


def test_relationship_saved_valid_reason() -> None:
    """Ensure that reason is saved properly in status other than expired or denied."""
    relationship = factories.Relationship()
    relationship.reason = 'Reason 1'
    relationship.status = RelationshipStatus.EXPIRED

    relationship.clean()
    assert relationship.reason == 'Reason 1'


def test_relationship_saved_reason_valid_denied() -> None:
    """Ensure that reason is saved properly in status denied."""
    relationship = factories.Relationship()
    relationship.reason = 'Reason 1'
    relationship.status = RelationshipStatus.DENIED

    relationship.clean()
    assert relationship.reason == 'Reason 1'


def test_relationship_saved_reason_valid_revoked() -> None:
    """Ensure that reason is saved properly in status revoked."""
    relationship = factories.Relationship()
    relationship.reason = 'Reason 1'
    relationship.status = RelationshipStatus.REVOKED

    relationship.clean()
    assert relationship.reason == 'Reason 1'


def test_relationship_same_combination() -> None:
    """Ensure that a relationship with same patient-caregiver-type-status combo is unique."""
    patient = factories.Patient(first_name='Kobe', last_name='Briant')
    caregiver = user_factories.Caregiver(first_name='John', last_name='Wayne')
    profile = factories.CaregiverProfile(user=caregiver)
    factories.Relationship(patient=patient, caregiver=profile)
    with assertRaisesMessage(IntegrityError, 'Duplicate entry'):  # type: ignore[arg-type]
        factories.Relationship(patient=patient, caregiver=profile)


def test_relationship_diff_relation_same_status() -> None:
    """Ensure that two unique patient-caregiver relationship doesn't prevent from sharing same status."""
    patient1 = factories.Patient(first_name='John', last_name='Smith')
    caregiver1 = user_factories.Caregiver(first_name='Betty', last_name='White')
    profile1 = factories.CaregiverProfile(user=caregiver1)
    factories.Relationship(patient=patient1, caregiver=profile1, status=RelationshipStatus.CONFIRMED)

    patient2 = factories.Patient(first_name='Will', last_name='Smith')
    caregiver2 = user_factories.Caregiver(first_name='Emma', last_name='Stone')
    profile2 = factories.CaregiverProfile(user=caregiver2)
    factories.Relationship(patient=patient2, caregiver=profile2, status=RelationshipStatus.CONFIRMED)


def test_relationship_diff_relation_same_type() -> None:
    """Ensure that two unique patient-caregiver relationship doesn't prevent from sharing same type."""
    patient1 = factories.Patient(first_name='John', last_name='Smith')
    caregiver1 = user_factories.Caregiver(first_name='Betty', last_name='White')
    profile1 = factories.CaregiverProfile(user=caregiver1)
    relationship1 = factories.Relationship.build(patient=patient1, caregiver=profile1)

    patient2 = factories.Patient(first_name='Will', last_name='Smith')
    caregiver2 = user_factories.Caregiver(first_name='Emma', last_name='Stone')
    profile2 = factories.CaregiverProfile(user=caregiver2)
    relationship2 = factories.Relationship.build(patient=patient2, caregiver=profile2)

    relationship1.type = factories.RelationshipType()
    relationship2.type = relationship1.type

    relationship1.full_clean()
    relationship2.full_clean()


def test_relationship_same_relation_diff_status() -> None:
    """Ensure that the unique patient-caregiver relationship doesn't prevent from having multiple statuses."""
    patient = factories.Patient(first_name='Will', last_name='Smith')
    caregiver = user_factories.Caregiver(first_name='Emma', last_name='Stone')
    profile = factories.CaregiverProfile(user=caregiver)
    factories.Relationship(patient=patient, caregiver=profile, status=RelationshipStatus.CONFIRMED)
    factories.Relationship(patient=patient, caregiver=profile, status=RelationshipStatus.PENDING)


def test_relationship_same_relation_diff_type() -> None:
    """Ensure that the unique patient-caregiver relationship doesn't prevent from having multiple types."""
    patient = factories.Patient(first_name='Will', last_name='Smith')
    caregiver = user_factories.Caregiver(first_name='Emma', last_name='Stone')
    profile = factories.CaregiverProfile(user=caregiver)

    type1 = factories.RelationshipType(name='Friend')
    type2 = factories.RelationshipType(name='Mentor')

    factories.Relationship(patient=patient, caregiver=profile, type=type1)
    factories.Relationship(patient=patient, caregiver=profile, type=type2)


def test_ivalid_date_of_death() -> None:
    """Ensure that the date of death is invalid if date of birth is later."""
    patient = factories.Patient()
    patient.date_of_birth = datetime.date(2022, 11, 20)
    patient.date_of_death = datetime.datetime(2022, 10, 20)

    expected_message = 'Date of death should be later than date of birth.'
    with assertRaisesMessage(ValidationError, expected_message):  # type: ignore[arg-type]
        patient.clean()


def test_valid_date_of_death() -> None:
    """Ensure that the date of death is entered and valid."""
    patient = factories.Patient()
    patient.date_of_birth = datetime.date(2022, 10, 20)
    patient.date_of_death = datetime.datetime(2022, 11, 20)

    patient.clean()
