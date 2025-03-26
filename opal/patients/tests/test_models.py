from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from django.utils import timezone

import pytest
from dateutil.relativedelta import relativedelta
from pytest_django.asserts import assertRaisesMessage

from opal.caregivers.models import CaregiverProfile
from opal.users import factories as user_factories

from .. import constants, factories
from ..models import (
    PREDEFINED_ROLE_TYPES,
    HospitalPatient,
    Patient,
    Relationship,
    RelationshipStatus,
    RelationshipType,
    RoleType,
)

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

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'Self' for key 'name'"):
        relationship_type = factories.RelationshipType.build(name='Self')
        relationship_type.save()


def test_relationshiptype_min_age_lowerbound() -> None:
    """Ensure the minimum age lower bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.start_age = constants.RELATIONSHIP_MIN_AGE - 1

    message = 'Ensure this value is greater than or equal to {0}.'.format(constants.RELATIONSHIP_MIN_AGE)

    with assertRaisesMessage(ValidationError, message):
        relationship_type.full_clean()

    relationship_type.start_age = constants.RELATIONSHIP_MIN_AGE
    relationship_type.full_clean()


def test_relationshiptype_min_age_upperbound() -> None:
    """Ensure the minimum age upper bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.start_age = constants.RELATIONSHIP_MAX_AGE

    message = 'Ensure this value is less than or equal to {0}.'.format(constants.RELATIONSHIP_MAX_AGE - 1)

    with assertRaisesMessage(ValidationError, message):
        relationship_type.full_clean()

    relationship_type.start_age = constants.RELATIONSHIP_MAX_AGE - 1
    relationship_type.full_clean()


def test_relationshiptype_max_age_lowerbound() -> None:
    """Ensure the maximum age lower bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.end_age = constants.RELATIONSHIP_MIN_AGE

    message = 'Ensure this value is greater than or equal to {0}.'.format(constants.RELATIONSHIP_MIN_AGE + 1)

    with assertRaisesMessage(ValidationError, message):
        relationship_type.full_clean()

    relationship_type.end_age = constants.RELATIONSHIP_MIN_AGE + 1
    relationship_type.full_clean()


def test_relationshiptype_max_age_upperbound() -> None:
    """Ensure the maximum age upper bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.end_age = constants.RELATIONSHIP_MAX_AGE + 1

    message = 'Ensure this value is less than or equal to {0}.'.format(constants.RELATIONSHIP_MAX_AGE)

    with assertRaisesMessage(ValidationError, message):
        relationship_type.full_clean()

    relationship_type.end_age = constants.RELATIONSHIP_MAX_AGE
    relationship_type.full_clean()


def test_relationshiptype_default_role() -> None:
    """Ensure a new relationshiptype (factory) role defaults to caregiver."""
    relationship_type = factories.RelationshipType()
    assert relationship_type.role_type == RoleType.CAREGIVER


def test_relationshiptype_is_self_true() -> None:
    """Ensure the RelationshipType correctly identifies a SELF role type."""
    relationship_type = factories.RelationshipType(role_type=RoleType.SELF)
    assert relationship_type.is_self


@pytest.mark.parametrize('role_type', [role for role in RoleType.values if role != RoleType.SELF])
def test_relationshiptype_is_self_false(role_type: RoleType) -> None:
    """Ensure the RelationshipType correctly identifies non-SELF role types."""
    relationship_type = factories.RelationshipType(role_type=role_type)
    assert not relationship_type.is_self


def test_patient_str() -> None:
    """Ensure the `__str__` method is defined for the `Patient` model."""
    patient = Patient(first_name='First Name', last_name='Last Name')
    assert str(patient) == 'Last Name, First Name'


def test_patient_age_calculation() -> None:
    """Ensure the `calculate_age` method calculate correctly for the `Patient` model."""
    date_of_birth = datetime(2004, 1, 1, 9, 20, 30)
    assert Patient.calculate_age(date_of_birth=date_of_birth) == 19


def test_patient_factory() -> None:
    """Ensure the Patient factory is building properly."""
    patient = factories.Patient()
    patient.full_clean()


def test_patient_factory_multiple() -> None:
    """Ensure the Patient factory can build multiple default model instances."""
    patient = factories.Patient()
    patient2 = factories.Patient()

    assert patient == patient2


def test_patient_uuid_unique() -> None:
    """Ensure that the field uuid of carigaver is unique."""
    patient = factories.Patient()
    patients2 = factories.Patient(ramq='SIMM87531908')
    patient.uuid = patients2.uuid

    message = 'Patient with this UUID already exists.'
    with assertRaisesMessage(ValidationError, message):
        patient.full_clean()


def test_patient_invalid_sex() -> None:
    """Ensure that a patient cannot be saved with an invalid sex type."""
    message = 'CONSTRAINT `patients_patient_sex_valid` failed'
    with assertRaisesMessage(IntegrityError, message):
        factories.Patient(sex='I')


def test_patient_ramq_non_unique() -> None:
    """Ensure that the health insurance number is non-unique."""
    factories.Patient(ramq='TEST12345678')
    factories.Patient(ramq='TEST12345678')


def test_patient_ramq_max() -> None:
    """Ensure the length of patient ramq is not greater than 12."""
    patient = factories.Patient()
    patient.ramq = 'ABCD5678901234'
    expected_message = '{0}, {1}'.format(
        "'ramq': ['Enter a valid RAMQ number consisting of 4 letters followed by 8 digits'",
        "'Ensure this value has at most 12 characters (it has 14).']",
    )
    with assertRaisesMessage(ValidationError, expected_message):
        patient.clean_fields()


def test_patient_ramq_min() -> None:
    """Ensure the length of patient ramq is not less than 12."""
    patient = factories.Patient(ramq='ABCD56')
    expected_message = '{0}'.format(
        "'ramq': ['Ensure this value has at least 12 characters (it has 6).'",
    )
    with assertRaisesMessage(ValidationError, expected_message):
        patient.clean_fields()


def test_patient_ramq_format() -> None:
    """Ensure the first 4 chars of patient ramq are alphabetic and last 8 chars are numeric."""
    patient = factories.Patient(ramq='ABC123456789')
    expected_message = '{0}'.format(
        "'ramq': ['Enter a valid RAMQ number consisting of 4 letters followed by 8 digits']",
    )
    with assertRaisesMessage(ValidationError, expected_message):
        patient.clean_fields()


def test_patient_legacy_id_unique() -> None:
    """Ensure that creating a second `Patient` with an existing `legacy_id` raises an `IntegrityError`."""
    factories.Patient(ramq='', legacy_id=1)
    message = "Duplicate entry '1' for key"

    with assertRaisesMessage(IntegrityError, message):
        factories.Patient(ramq='somevalue', legacy_id=1)


def test_patient_non_existing_legacy_id() -> None:
    """Ensure that creating a second `Patient` with a non-existing legacy_id does not raise a `ValidationError`."""
    factories.Patient(ramq='', legacy_id=None)
    factories.Patient(ramq='somevalue', legacy_id=None)

    assert Patient.objects.count() == 2


def test_patient_access_level_default() -> None:
    """Ensure that the default data access level is ALL."""
    patient = factories.Patient()

    assert patient.data_access == Patient.DataAccessType.ALL


def test_patient_non_interpretable_delay_field_required() -> None:
    """Make sure that non interpretable lab result delay is required."""
    with assertRaisesMessage(IntegrityError, "Column 'non_interpretable_lab_result_delay' cannot be null"):
        factories.Patient(non_interpretable_lab_result_delay=None)


def test_patient_non_interpretable_delay_field_min_value() -> None:
    """Make sure that non interpretable lab result delay is greater than or equal to 0."""
    with assertRaisesMessage(DataError, "Out of range value for column 'non_interpretable_lab_result_delay' at row 1"):
        factories.Patient(non_interpretable_lab_result_delay=-1)


def test_patient_non_interpretable_delay_field_max_value() -> None:
    """Make sure that non interpretable lab result delay is less than or equal to 99."""
    patient = factories.Patient(non_interpretable_lab_result_delay=100)

    with assertRaisesMessage(ValidationError, 'Ensure this value is less than or equal to 99.'):
        patient.full_clean()


def test_patient_interpretable_delay_field_required() -> None:
    """Make sure that interpretable lab result delay is required."""
    with assertRaisesMessage(IntegrityError, "Column 'interpretable_lab_result_delay' cannot be null"):
        factories.Patient(interpretable_lab_result_delay=None)


def test_patient_interpretable_delay_field_min_value() -> None:
    """Make sure that interpretable lab result delay is greater than or equal to 0."""
    with assertRaisesMessage(DataError, "Out of range value for column 'interpretable_lab_result_delay' at row 1"):
        factories.Patient(interpretable_lab_result_delay=-1)


def test_patient_interpretable_delay_field_max_value() -> None:
    """Make sure that interpretable lab result delay is less than or equal to 99."""
    patient = factories.Patient(interpretable_lab_result_delay=100)

    with assertRaisesMessage(ValidationError, 'Ensure this value is less than or equal to 99.'):
        patient.full_clean()


def test_relationship_str() -> None:
    """Ensure the `__str__` method is defined for the `Relationship` model."""
    patient = factories.Patient(first_name='Kobe', last_name='Briant')

    caregiver = user_factories.Caregiver(first_name='John', last_name='Wayne')
    profile = CaregiverProfile(user=caregiver)

    relationship = factories.Relationship.build(patient=patient, caregiver=profile)

    assert str(relationship) == 'Briant, Kobe <--> Wayne, John [Caregiver]'


def test_relationship_factory() -> None:
    """Ensure the Relationship factory is building properly."""
    relationship = factories.Relationship()
    relationship.full_clean()


def test_relationship_factory_multiple() -> None:
    """Ensure the Relationship factory can build multiple default model instances."""
    relationship = factories.Relationship()
    relationship2 = factories.Relationship()
    relationship2.full_clean()

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
    relationship = factories.Relationship(
        start_date=date.fromisoformat('2022-05-04'),
        end_date=None,
    )

    relationship.clean_fields()
    relationship.clean()


def test_relationship_clean_no_data() -> None:
    """Ensure that the relationship validation works with missing data."""
    relationship = Relationship()
    assert hasattr(relationship, 'start_date')
    assert relationship.start_date is None

    relationship.clean()


def test_relationship_clean_no_patient_caregiver() -> None:
    """Ensure that the relationship validation works with a missing patient and caregiver."""
    relationship = Relationship(
        type=RelationshipType.objects.self_type(),
        status=RelationshipStatus.CONFIRMED,
    )

    relationship.clean()


def test_relationship_clean_valid_dates() -> None:
    """Ensure that the date is valid if start date is earlier than end date."""
    relationship = factories.Relationship(
        start_date=date.fromisoformat('2022-05-01'),
        end_date=date.fromisoformat('2022-05-04'),
    )

    relationship.clean_fields()
    relationship.clean()


def test_relationship_clean_invalid_dates() -> None:
    """Ensure that the date is invalid if start date is later than end date."""
    relationship = factories.Relationship()
    relationship.start_date = date(2022, 5, 8)
    relationship.end_date = date(2022, 5, 4)

    expected_message = 'Start date should be earlier than end date.'
    with assertRaisesMessage(ValidationError, expected_message):
        relationship.clean()


def test_relationship_clean_start_date_before_date_of_birth() -> None:
    """Ensure that the relationship start_date cannot be before the patient's date of birth."""
    relationship = factories.Relationship()
    relationship.start_date = relationship.patient.date_of_birth - timedelta(days=1)

    expected_message = "Start date cannot be earlier than patient's date of birth"
    with assertRaisesMessage(ValidationError, expected_message):
        relationship.clean()


def test_relationship_clean_end_date_beyond_boundary() -> None:
    """Ensure that the relationship end_date cannot be before the boundary."""
    relationship = factories.Relationship()
    relationship.patient.date_of_birth = date(2008, 5, 9)
    relationship.type.end_age = 18

    calculated_end_date = relationship.patient.date_of_birth + relativedelta(
        years=relationship.type.end_age,
    )
    relationship.start_date = calculated_end_date - relativedelta(years=2)
    relationship.end_date = calculated_end_date + timedelta(days=1)

    expected_message = 'End date for Caregiver relationship cannot be later than {calculated_end_date}.'.format(
        calculated_end_date=calculated_end_date,
    )
    with assertRaisesMessage(ValidationError, expected_message):
        relationship.clean()


def test_relationship_clean_pending_not_apply_self_role() -> None:
    """Ensure that the relationship Pending status does not apply for the Self relationship."""
    self_type = RelationshipType.objects.self_type()
    relationship = factories.Relationship(type=self_type)
    relationship.status = RelationshipStatus.PENDING

    expected_message = '"Pending" status does not apply for the Self relationship.'
    with assertRaisesMessage(ValidationError, expected_message):
        relationship.clean()


def test_relationship_clean_no_patient_multiple_self() -> None:
    """Ensure that a patient can only have one self-relationship."""
    self_type = RelationshipType.objects.self_type()

    relationship = factories.Relationship(type=self_type)
    # create a relationship with a new relationship type
    relationship2 = factories.Relationship(patient=relationship.patient)
    relationship2.full_clean()

    relationship2.type = self_type

    with assertRaisesMessage(ValidationError, 'The patient already has a self-relationship.'):
        relationship2.full_clean()


def test_relationship_clean_no_caregiver_multiple_self() -> None:
    """Ensure that a caregiver can only have one self-relationship."""
    self_type = RelationshipType.objects.self_type()

    relationship = factories.Relationship(type=self_type)
    # create a relationship with a new relationship type and patient
    patient = factories.Patient(ramq='SIMM86100299')
    relationship2 = factories.Relationship(patient=patient, caregiver=relationship.caregiver)
    relationship2.full_clean()

    relationship2.type = self_type

    with assertRaisesMessage(ValidationError, 'The caregiver already has a self-relationship.'):
        relationship2.full_clean()


@pytest.mark.parametrize('status', [
    RelationshipStatus.CONFIRMED,
    RelationshipStatus.PENDING,
])
def test_relationship_clean_no_caregiver_multiple_active_relationships(status: RelationshipStatus) -> None:
    """Ensure that a caregiver cannot have multiple active relationships to the same patient."""
    self_type = RelationshipType.objects.self_type()

    relationship = factories.Relationship(type=self_type, status=status)
    # create a relationship with a new relationship type
    relationship2 = Relationship(
        patient=relationship.patient,
        caregiver=relationship.caregiver,
        status=RelationshipStatus.PENDING,
        type=RelationshipType.objects.mandatary(),
    )

    with assertRaisesMessage(
        ValidationError,
        'There already exists an active relationship between the patient and caregiver.',
    ):
        relationship2.clean()

    # create a relationship with a new relationship type
    relationship3 = Relationship(
        patient=relationship.patient,
        caregiver=relationship.caregiver,
        status=RelationshipStatus.CONFIRMED,
        type=RelationshipType.objects.mandatary(),
    )

    with assertRaisesMessage(
        ValidationError,
        'There already exists an active relationship between the patient and caregiver.',
    ):
        relationship3.clean()


def test_relationship_clean_can_update_existing_self() -> None:
    """Ensure that an existing self-relationship can be updated."""
    self_type = RelationshipType.objects.self_type()

    relationship = factories.Relationship(type=self_type)
    relationship.status = RelationshipStatus.CONFIRMED
    relationship.end_date = None  # type: ignore[assignment]
    relationship.full_clean()


def test_relationship_clean_self_patient_caregiver_names_mismatch() -> None:
    """Ensure that a name mismatch between patient and caregiver for a self-relationship is detected."""
    self_type = RelationshipType.objects.self_type()

    relationship = factories.Relationship(
        patient__first_name='Marge',
        patient__last_name='Simpson',
        type=self_type,
        status=RelationshipStatus.CONFIRMED,
        caregiver__user__first_name='Marge',
        caregiver__user__last_name='Simpson',
    )
    relationship.full_clean()

    with assertRaisesMessage(
        ValidationError,
        'A self-relationship was selected but the caregiver appears to be someone other than the patient.',
    ):
        relationship.patient.first_name = 'Homer'
        relationship.full_clean()

    with assertRaisesMessage(
        ValidationError,
        'A self-relationship was selected but the caregiver appears to be someone other than the patient.',
    ):
        relationship.patient.first_name = 'Marge'
        relationship.patient.last_name = 'Flanders'
        relationship.full_clean()


def test_relationship_clean_unsaved_instance() -> None:
    """Ensure that an unsaved relationship instance can be cleaned."""
    self_type = RelationshipType.objects.self_type()

    patient = factories.Patient()
    caregiver = factories.CaregiverProfile()
    relationship = factories.Relationship.build(patient=patient, caregiver=caregiver, type=self_type)
    relationship.status = RelationshipStatus.CONFIRMED

    relationship.full_clean()


def test_relationship_invalid_dates_constraint() -> None:
    """Ensure that the date cannot be saved if start date is later than end date."""
    relationship = factories.Relationship()
    relationship.start_date = date(2022, 5, 8)
    relationship.end_date = date(2022, 5, 4)

    constraint_name = 'patients_relationship_date_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):
        relationship.save()


def test_relationship_status_constraint() -> None:
    """Error happens when assigning an invalid Relationship status."""
    relationship = factories.Relationship()
    relationship.status = 'INV'

    constraint_name = 'patients_relationship_status_valid'
    with assertRaisesMessage(IntegrityError, constraint_name):
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
    site = factories.Site(name="Montreal Children's Hospital")
    hospital_patient = factories.HospitalPatient(site=site)

    assert str(hospital_patient) == 'MONT: 9999996'


def test_hospitalpatient_one_patient_many_sites() -> None:
    """Ensure a patient can have MRNs at different sites."""
    patient = factories.Patient(first_name='aaa', last_name='bbb')
    site1 = factories.Site(name="Montreal Children's Hospital")
    site2 = factories.Site(name='Royal Victoria Hospital')

    HospitalPatient.objects.create(patient=patient, site=site1, mrn='9999996')
    HospitalPatient.objects.create(patient=patient, site=site2, mrn='9999996')

    assert HospitalPatient.objects.count() == 2

    with assertRaisesMessage(IntegrityError, 'Duplicate entry'):
        HospitalPatient.objects.create(patient=patient, site=site1, mrn='9999996')


def test_hospitalpatient_many_patients_one_site() -> None:
    """Ensure a (site, MRN) pair can only be used once."""
    patient1 = factories.Patient(first_name='aaa', last_name='111')
    patient2 = factories.Patient(
        first_name='bbb',
        last_name='222',
    )
    site = factories.Site(name="Montreal Children's Hospital")

    HospitalPatient.objects.create(patient=patient1, site=site, mrn='9999996')

    with assertRaisesMessage(IntegrityError, 'Duplicate entry'):
        HospitalPatient.objects.create(patient=patient2, site=site, mrn='9999996')


def test_hospitalpatient_patient_site_unique() -> None:
    """Ensure a patient can only have one MRN at a specific site."""
    patient = factories.Patient()
    site = factories.Site()

    HospitalPatient.objects.create(patient=patient, site=site, mrn='9999996')

    expected_message = r"Duplicate entry '(\d+\-\d+)' for key 'patients_hospitalpatient_patient_id_site_id_(\d+)_uniq"
    with pytest.raises(IntegrityError, match=expected_message):
        HospitalPatient.objects.create(patient=patient, site=site, mrn='9999997')


def test_can_answer_questionnaire_default() -> None:
    """Ensure default can_answer_questionnaire field is false."""
    relationtype = factories.RelationshipType()
    assert not relationtype.can_answer_questionnaire


# tests for reason field constraints and validations
def test_relationship_no_reason_invalid_revoked() -> None:
    """Ensure that error is thrown when reason is empty and status is revoked."""
    relationship = factories.Relationship()
    relationship.reason = ''
    relationship.status = RelationshipStatus.REVOKED

    expected_message = 'Reason is mandatory when status is denied or revoked.'
    with assertRaisesMessage(ValidationError, expected_message):
        relationship.clean()


def test_relationship_no_reason_invalid_denied() -> None:
    """Ensure that error is thrown when reason is empty and status is denied."""
    relationship = factories.Relationship()
    relationship.reason = ''
    relationship.status = RelationshipStatus.DENIED

    expected_message = 'Reason is mandatory when status is denied or revoked.'
    with assertRaisesMessage(ValidationError, expected_message):
        relationship.clean()


def test_relationship_valid_reason_pass_denied() -> None:
    """Ensure that error is not thrown when reason field has content and status is denied."""
    relationship = factories.Relationship(reason='A reason')
    relationship.status = RelationshipStatus.DENIED

    relationship.clean()


def test_relationship_valid_reason_pass_revoked() -> None:
    """Ensure that error is not thrown when reason field has content and status is revoked."""
    relationship = factories.Relationship(reason='A reason')
    relationship.status = RelationshipStatus.REVOKED

    relationship.clean()


def test_relationship_reason_non_required_status() -> None:
    """Ensure that a reason field can be provided for a status that does not require one."""
    relationship = factories.Relationship(reason='A reason')
    relationship.status = RelationshipStatus.CONFIRMED

    relationship.clean()


def test_relationship_same_combination() -> None:
    """Ensure that a relationship with same patient-caregiver-type-status combo is unique."""
    patient = factories.Patient(first_name='Kobe', last_name='Briant')
    caregiver = user_factories.Caregiver(first_name='John', last_name='Wayne')
    profile = factories.CaregiverProfile(user=caregiver)
    factories.Relationship(patient=patient, caregiver=profile)
    with assertRaisesMessage(IntegrityError, 'Duplicate entry'):
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


def test_invalid_date_of_death() -> None:
    """Ensure that the date of death is invalid if date of birth is later."""
    patient = factories.Patient()
    patient.date_of_birth = date(2022, 11, 20)
    patient.date_of_death = timezone.make_aware(datetime(2022, 10, 20))

    expected_message = 'Date of death cannot be earlier than date of birth.'
    with assertRaisesMessage(ValidationError, expected_message):
        patient.clean()


def test_valid_date_of_death() -> None:
    """Ensure that the date of death is entered and valid."""
    patient = factories.Patient()
    patient.date_of_birth = date(2022, 10, 20)
    patient.date_of_death = timezone.make_aware(datetime(2022, 11, 20))

    patient.clean()


def test_same_birth_and_death_date() -> None:
    """Ensure that the date of death is valid if same as date of birth."""
    patient = factories.Patient()
    patient.date_of_birth = date(2022, 1, 23)
    patient.date_of_death = timezone.make_aware(datetime(2022, 1, 23))

    patient.clean()


@pytest.mark.parametrize(
    'initial_status',
    [
        RelationshipStatus.DENIED,
        RelationshipStatus.CONFIRMED,
        RelationshipStatus.PENDING,
        RelationshipStatus.REVOKED,
        RelationshipStatus.EXPIRED,
    ],
)
def test_validstatuses_contain_initial_status(initial_status: RelationshipStatus) -> None:
    """Ensure that the returned list of statuses includes the initial status."""
    validstatuses = Relationship.valid_statuses(initial_status)

    assert initial_status in validstatuses


def test_validstatuses_not_contain_wrong_status_pending() -> None:
    """Ensure that valid statuses do no contain wrong status for PENDING."""
    initial_status = RelationshipStatus.PENDING
    validstatuses = Relationship.valid_statuses(initial_status)

    assert RelationshipStatus.REVOKED not in validstatuses
    assert RelationshipStatus.EXPIRED not in validstatuses


def test_validstatuses_not_contain_wrong_status_confirmed() -> None:
    """Ensure that valid statuses do no contain wrong status for CONFIRMED."""
    initial_status = RelationshipStatus.CONFIRMED
    validstatuses = Relationship.valid_statuses(initial_status)

    assert RelationshipStatus.DENIED not in validstatuses


def test_validstatuses_not_contain_wrong_status_denied() -> None:
    """Ensure that valid statuses do no contain wrong status for DENIED."""
    initial_status = RelationshipStatus.DENIED
    validstatuses = Relationship.valid_statuses(initial_status)

    assert RelationshipStatus.EXPIRED not in validstatuses
    assert RelationshipStatus.REVOKED not in validstatuses


def test_validstatuses_not_contain_wrong_status_revoked() -> None:
    """Ensure that valid statuses do no contain wrong status for REVOKED."""
    initial_status = RelationshipStatus.REVOKED
    validstatuses = Relationship.valid_statuses(initial_status)

    assert RelationshipStatus.DENIED not in validstatuses
    assert RelationshipStatus.EXPIRED not in validstatuses
    assert RelationshipStatus.PENDING not in validstatuses


def test_validstatuses_not_contain_wrong_status_expired() -> None:
    """Ensure that valid statuses do no contain wrong status for EXPIRED."""
    initial_status = RelationshipStatus.EXPIRED
    validstatuses = Relationship.valid_statuses(initial_status)

    assert RelationshipStatus.DENIED not in validstatuses
    assert RelationshipStatus.CONFIRMED not in validstatuses
    assert RelationshipStatus.PENDING not in validstatuses
    assert RelationshipStatus.REVOKED not in validstatuses


@pytest.mark.parametrize(
    ('initial_status', 'expected_statuses'),
    [
        (
            RelationshipStatus.PENDING,
            [
                RelationshipStatus.PENDING,
                RelationshipStatus.DENIED,
                RelationshipStatus.CONFIRMED,
            ],
        ),
        (
            RelationshipStatus.CONFIRMED,
            [
                RelationshipStatus.CONFIRMED,
                RelationshipStatus.PENDING,
                RelationshipStatus.REVOKED,
            ],
        ),
        (
            RelationshipStatus.DENIED,
            [
                RelationshipStatus.DENIED,
                RelationshipStatus.CONFIRMED,
                RelationshipStatus.PENDING,
            ],
        ),
        (
            RelationshipStatus.REVOKED,
            [
                RelationshipStatus.REVOKED,
                RelationshipStatus.CONFIRMED,
            ],
        ),
        (
            RelationshipStatus.EXPIRED,
            [
                RelationshipStatus.EXPIRED,
            ],
        ),
    ],
)
def test_validstatuses_contain_correct_statuses(
    initial_status: RelationshipStatus,
    expected_statuses: list[RelationshipStatus],
) -> None:
    """Ensure that the returned list of statuses is correct."""
    validstatuses = Relationship.valid_statuses(initial_status)

    assert validstatuses == expected_statuses


@pytest.mark.parametrize(
    ('date_of_birth', 'request_date', 'role_type', 'expected'),
    [
        (
            date(2004, 1, 1),
            date(2023, 4, 24),
            RoleType.SELF,
            date(2004, 1, 1),
        ),
        (
            date(2004, 1, 1),
            date(2023, 4, 24),
            RoleType.PARENT_GUARDIAN,
            date(2004, 1, 1),
        ),
        (
            date(2004, 1, 1),
            date(2023, 4, 24),
            RoleType.GUARDIAN_CAREGIVER,
            date(2004, 1, 1),
        ),
        (
            date(2004, 1, 1),
            date(2023, 4, 24),
            RoleType.MANDATARY,
            date(2023, 4, 24),
        ),
    ],
)
def test_relationship_calculate_default_start_date(
    date_of_birth: date,
    request_date: date,
    role_type: RoleType,
    expected: date,
) -> None:
    """Test set relationship start date for adult patient."""
    relationship_type = RelationshipType.objects.get(role_type=role_type)

    assert (
        Relationship.calculate_default_start_date(
            request_date=request_date,
            date_of_birth=date_of_birth,
            relationship_type=relationship_type,
        )
        == expected
    )


def test_relationship_calculate_end_date_with_end_age_set() -> None:
    """Test set relationship end date if a relationship type has an end age set."""
    date_of_birth = date(2013, 4, 3)
    relationship_type = factories.RelationshipType(name='Guardian-Caregiver', start_age=14, end_age=18)

    assert Relationship.calculate_end_date(
        date_of_birth=date_of_birth,
        relationship_type=relationship_type,
    ) == date_of_birth + relativedelta(years=relationship_type.end_age)


def test_relationship_calculate_end_date_actual_value() -> None:
    """Test set relationship end date if it is an actual date value."""
    date_of_birth = date(2013, 4, 3)
    relationship_type = factories.RelationshipType(name='Guardian-Caregiver', start_age=14, end_age=18)

    assert Relationship.calculate_end_date(
        date_of_birth=date_of_birth,
        relationship_type=relationship_type,
    ) == date(2031, 4, 3)


def test_relationship_calculate_end_date_without_end_age_set() -> None:
    """Test set relationship end date if a relationship type has no end age set."""
    date_of_birth = date(2013, 4, 3)
    relationship_type = factories.RelationshipType(name='Mandatary', start_age=1)

    assert (
        Relationship.calculate_end_date(
            date_of_birth=date_of_birth,
            relationship_type=relationship_type,
        )
        is None
    )


def test_relationshiptype_default() -> None:
    """Ensure there are two relationship types by default."""
    assert RelationshipType.objects.count() == 4

    # ensure that there is one of each
    RelationshipType.objects.get(role_type=RoleType.SELF)
    RelationshipType.objects.get(role_type=RoleType.PARENT_GUARDIAN)
    RelationshipType.objects.get(role_type=RoleType.GUARDIAN_CAREGIVER)
    RelationshipType.objects.get(role_type=RoleType.MANDATARY)


@pytest.mark.parametrize('role_type', PREDEFINED_ROLE_TYPES)
def test_relationshiptype_predefined_role_type_delete_error(role_type: RoleType) -> None:
    """Ensure the user can not delete a self role type."""
    relationship_type = RelationshipType.objects.get(role_type=role_type)

    message = "['The relationship type with this role type cannot be deleted']"
    with assertRaisesMessage(ValidationError, message):
        relationship_type.delete()


@pytest.mark.parametrize('role_type', PREDEFINED_ROLE_TYPES)
def test_relationshiptype_duplicate_predefined_role_type(role_type: RoleType) -> None:
    """Ensure validation error when creating a second predefined role type."""
    relationship_type = factories.RelationshipType()
    relationship_type.role_type = role_type

    message = "['There already exists a relationship type with this role type']"
    with assertRaisesMessage(ValidationError, message):
        relationship_type.full_clean()


@pytest.mark.parametrize('role_type', PREDEFINED_ROLE_TYPES)
def test_relationshiptype_can_update_predefined_role_type(role_type: RoleType) -> None:
    """Ensure validation error when creating a second predefined role type."""
    relationship_type = RelationshipType.objects.get(role_type=role_type)

    relationship_type.name = 'Changed Name'
    relationship_type.full_clean()


def test_relationshiptype_can_add_caregiver_type() -> None:
    """Ensure a relationship type with a role type of `CAREGIVER` can be created."""
    relationship_type = factories.RelationshipType(role_type=RoleType.CAREGIVER)
    relationship_type.full_clean()


def test_relationshiptype_can_delete_caregiver_type() -> None:
    """Ensure a relationship type with a role type of `CAREGIVER` can be deleted."""
    relationship_type = factories.RelationshipType(role_type=RoleType.CAREGIVER)
    relationship_type.delete()
