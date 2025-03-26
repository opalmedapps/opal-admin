"""App patients util functions."""
import logging
from datetime import date
from typing import Any, Final, Optional
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from opal.caregivers import models as caregiver_models
from opal.core.utils import generate_random_registration_code, generate_random_uuid
from opal.hospital_settings.models import Site
from opal.legacy import utils as legacy_utils
from opal.legacy.models import LegacyUserType
from opal.services.hospital.hospital import OIEService
from opal.services.hospital.hospital_data import OIEPatientData
from opal.services.orms.orms import ORMSService
from opal.users.models import Caregiver, User

from .models import HospitalPatient, Patient, Relationship, RelationshipStatus, RelationshipType, RoleType

#: The indicator of the female sex within the RAMQ number (added to the month)
RAMQ_FEMALE_INDICATOR: Final = 50
#: Length of the random username
RANDOM_USERNAME_LENGTH: Final = 16
#: Length for the registration code excluding the two character prefix.
REGISTRATION_CODE_LENGTH: Final = 10

# Initialize services to communicate with external components
oie_service: OIEService = OIEService()
orms_service: ORMSService = ORMSService()

logger = logging.getLogger(__name__)


def build_ramq(first_name: str, last_name: str, date_of_birth: date, sex: Patient.SexType) -> str:
    """
    Build a RAMQ number based on the official format and with 99 as the last two digits (administrative code).

    See: https://www.ramq.gouv.qc.ca/en/citizens/health-insurance/using-card

    Args:
        first_name: the person's first name
        last_name: the person's last name
        date_of_birth: the person's date of birth
        sex: the person's sex

    Returns:
        the RAMQ number derived from the given arguments
    """
    month = (
        date_of_birth.strftime('%m')
        if sex == Patient.SexType.MALE
        else date_of_birth.month + RAMQ_FEMALE_INDICATOR
    )

    data = [
        last_name[:3].upper(),
        first_name[0].upper(),
        date_of_birth.strftime('%y'),
        str(month),
        date_of_birth.strftime('%d'),
        '99',
    ]

    return ''.join(data)


def update_registration_code_status(
    registration_code: caregiver_models.RegistrationCode,
) -> None:
    """
    Get and update RegistrationCode status from NEW to REGISTERED.

    Args:
        registration_code: registration code object.
    """
    registration_code.status = caregiver_models.RegistrationCodeStatus.REGISTERED
    registration_code.full_clean()
    registration_code.save()


def update_patient_legacy_id(patient: Patient, legacy_id: int) -> None:
    """
    Update Patient Legacy_id.

    Args:
        patient: Patient object
        legacy_id: number or None.
    """
    patient.legacy_id = legacy_id
    patient.full_clean()
    patient.save()


def find_caregiver(username: str) -> Optional[User]:
    """
    Find the user if it exists.

    Args:
        username: caregiver username

    Returns:
        return caregiver if the caregiver eixsts otherwise return None
    """
    return Caregiver.objects.filter(username=username).first()


def update_caregiver(user: User, info: dict[str, Any]) -> None:
    """
    Update User information.

    Args:
        user: User object
        info: User info to be updated
    """
    user.username = info['user']['username']
    user.language = info['user']['language']
    user.phone_number = info['user']['phone_number']
    user.date_joined = timezone.now()
    user.is_active = True
    user.full_clean()
    user.save()


def replace_caregiver(existing_caregiver: User, relationship: Relationship) -> None:
    """
    Re-link the relationship to the existing caregiver_profile.

    And delete the skeleton caregiver_profile and skeleton caregiver

    Args:
        existing_caregiver: Caregiver object
        relationship: Relationship object
    """
    old_skeleton_user = relationship.caregiver.user
    old_skeleton_profile = relationship.caregiver
    existing_profile = caregiver_models.CaregiverProfile.objects.get(user=existing_caregiver)
    relationship.caregiver = existing_profile
    relationship.full_clean()
    relationship.save()
    old_skeleton_profile.delete()
    old_skeleton_user.delete()


def update_caregiver_profile(profile: caregiver_models.CaregiverProfile, info: dict[str, Any]) -> None:
    """
    Update CaregiverProfile information.

    Args:
        profile: CaregiverProfile object
        info: Caregiver info to be updated
    """
    profile.legacy_id = info['legacy_id']
    profile.full_clean()
    profile.save()


def insert_security_answers(
    caregiver_profile: caregiver_models.CaregiverProfile,
    security_answers: list,
) -> None:
    """
    Insert security answers.

    Args:
        caregiver_profile: CaregiverProfile object
        security_answers: list of security answer data
    """
    answers = [caregiver_models.SecurityAnswer(**answer, user=caregiver_profile) for answer in security_answers]
    caregiver_models.SecurityAnswer.objects.bulk_create(answers)


def search_relationship_types_by_patient_age(date_of_birth: date) -> QuerySet[RelationshipType]:
    """
    Search for valid relationship types according to the patient's age.

    Args:
        date_of_birth: date of birth of the patient

    Returns:
        Queryset of relationship types according to the patient's age
    """
    age = Patient.calculate_age(date_of_birth=date_of_birth)
    return RelationshipType.objects.filter_by_patient_age(patient_age=age)  # type: ignore[no-any-return]


def valid_relationship_types(patient: Patient) -> QuerySet[RelationshipType]:
    """
    Get the queryset of valid relationship types according to the patient's age and existing self role.

    Args:
        patient: Patient object

    Returns:
        Queryset of valid relationship types
    """
    relationship_types_queryset = search_relationship_types_by_patient_age(patient.date_of_birth)

    if Relationship.objects.filter(
        patient=patient,
        type__role_type=RoleType.SELF,
    ).exists():
        return relationship_types_queryset.exclude(role_type=RoleType.SELF)

    return relationship_types_queryset


def get_patient_by_ramq_or_mrn(ramq: Optional[str], mrn: str, site: str) -> Optional[Patient]:
    """
    Get a `Patient` object filtered by a given RAMQ or sites and MRNs.

    Args:
        ramq: patient's RAMQ
        mrn: patient's MRN
        site: patient's site code

    Returns:
        `Patient` object
    """
    if ramq:
        return Patient.objects.filter(ramq=ramq).first()
    return Patient.objects.filter(
        hospital_patients__mrn=mrn,
        hospital_patients__site__code=site,
    ).first()


def create_caregiver_profile(first_name: str, last_name: str) -> caregiver_models.CaregiverProfile:
    """
    Create new caregiver and caregiver profile instances.

    The caregiver profile is associated to the caregiver.
    The caregiver has a randomly generated username and is not active by default to require registration first.
    The caregiver also only has a first and last name.
    No email or password.

    Args:
        first_name: the first name of the caregiver
        last_name: the last name of the caregiver

    Returns:
        the caregiver profile instance, access the caregiver via the `user` property
    """
    caregiver = Caregiver.objects.create(
        # define a random username since an empty username can only exist once
        username=generate_random_uuid(RANDOM_USERNAME_LENGTH),
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )
    # User passwords aren't currently saved in Django
    caregiver.set_unusable_password()
    caregiver.full_clean()
    caregiver.save()

    return caregiver_models.CaregiverProfile.objects.create(user=caregiver)


def create_patient(  # noqa: WPS211
    first_name: str,
    last_name: str,
    date_of_birth: date,
    sex: Patient.SexType,
    ramq: str,
    mrns: list[tuple[Site, str, bool]],
) -> Patient:
    """
    Create a new patient instance and associated HospitalPatient instances (if necessary).

    Args:
        first_name: the patient's first name
        last_name: the patient's last name
        date_of_birth: the patient's date of birth
        sex: the patient's sex
        ramq: the patient's RAMQ, None if the patient has none
        mrns: list of MRN tuples consisting of the site, MRN and whether the MRN is active

    Returns:
        the new patient instance
    """
    patient = Patient(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        sex=sex,
        ramq=ramq,
    )

    patient.full_clean()
    patient.save()

    hospital_patients = [
        HospitalPatient(
            patient=patient,
            site=site,
            mrn=mrn,
            is_active=is_active,
        )
        for (site, mrn, is_active) in mrns
    ]
    HospitalPatient.objects.bulk_create(hospital_patients)

    return patient


def create_relationship(  # noqa: WPS211
    patient: Patient,
    caregiver_profile: caregiver_models.CaregiverProfile,
    relationship_type: RelationshipType,
    status: RelationshipStatus,
    request_date: Optional[date] = None,
    start_date: Optional[date] = None,
) -> Relationship:
    """
    Create a new relationship instance with the given properties.

    Args:
        patient: the patient instance
        caregiver_profile: the caregiver profile instance
        relationship_type: the type of the relationship
        status: the status of the relationship
        request_date: the request date of the relationship, defaults to today's date if None
        start_date: the start date of the relationship, defaults to the patient's date of birth if None

    Returns:
        the new relationship instance
    """
    if not request_date:
        request_date = date.today()

    if not start_date:
        start_date = patient.date_of_birth

    end_date = Relationship.calculate_end_date(
        patient.date_of_birth,
        relationship_type,
    )

    relationship = Relationship(
        patient=patient,
        caregiver=caregiver_profile,
        type=relationship_type,
        status=status,
        request_date=request_date,
        start_date=start_date,
        end_date=end_date,
    )

    relationship.full_clean()
    relationship.save()

    return relationship


def create_registration_code(relationship: Relationship) -> caregiver_models.RegistrationCode:
    """
    Create a new registration code instance associated with the given relationship.

    The code for the `RegistrationCode` is randomly generated and prefixed with the `INSTITUTION_CODE`
    defined in the settings.

    Args:
        relationship: the relationship the registration code is for

    Returns:
        the new registration code instance
    """
    code = generate_random_registration_code(settings.INSTITUTION_CODE, REGISTRATION_CODE_LENGTH)
    registration_code = caregiver_models.RegistrationCode(
        relationship=relationship,
        code=code,
    )

    registration_code.full_clean()
    registration_code.save()

    return registration_code


def initialize_new_opal_patient(mrn_list: list[tuple[Site, str, bool]], patient_uuid: UUID) -> None:
    """
    Execute all the steps necessary to set up a new patient in the system after registration.

    This includes notifying ORMS and the OIE of the new patient.

    Args:
        mrn_list: A list of (site, mrn, is_active) tuples representing the patient's MRNs.
        patient_uuid: The new patient's Patient UUID.
    """
    # Initialize the patient's data in the legacy database
    # TODO

    # Call ORMS to notify it of the existence of the new patient
    active_mrn_list = [(site.code, mrn) for site, mrn, is_active in mrn_list if is_active]
    orms_response = orms_service.set_opal_patient(active_mrn_list, patient_uuid)

    if orms_response['status'] == 'success':
        logger.info('Successfully initialized patient via ORMS; patient_uuid = {0}'.format(patient_uuid))
    else:
        logger.error('Failed to initialize patient via ORMS')
        logger.error(
            'MRNs = {0}, patient_uuid = {1}, ORMS response = {2}'.format(mrn_list, patient_uuid, orms_response),
        )

    # Call the OIE to notify it of the existence of the new patient
    # TODO


@transaction.atomic
def create_access_request(  # noqa: WPS210 (too many local variables)
    patient: Patient | OIEPatientData,
    caregiver: caregiver_models.CaregiverProfile | tuple[str, str],
    relationship_type: RelationshipType,
) -> tuple[Relationship, Optional[caregiver_models.RegistrationCode]]:
    """
    Create a new access request (relationship) between the patient and caregiver.

    The patient/caregiver may be already existent or a new one.
    If the patient/caregiver is new, a new instance will be created.
    For a new caregiver a registration code will also be created.

    Args:
        patient: a `Patient` instance if the patient exists, `OIEPatientData` otherwise
        caregiver: a `Caregiver` instance if the caregiver exists, a tuple consisting of first and last name otherwise
        relationship_type: the type of relationship between the caregiver and patient

    Raises:
        ValueError: if an existing user registering as self is missing their legacy_id value

    Returns:
        the newly created relationship (which provides access to patient and caregiver)
        and the registration code (in the case of a new caregiver, otherwise None)
    """
    is_new_patient = False
    registration_code = None
    mrns = []
    status = (
        RelationshipStatus.CONFIRMED if relationship_type.role_type == RoleType.SELF else RelationshipStatus.PENDING
    )

    # New patient
    if isinstance(patient, OIEPatientData):
        is_new_patient = True
        mrns = [
            (Site.objects.get(code=mrn_data.site), mrn_data.mrn, mrn_data.active)
            for mrn_data in patient.mrns
        ]

        patient = create_patient(
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            sex=Patient.SexType(patient.sex),
            ramq=patient.ramq,
            mrns=mrns,
        )

    # TODO: check whether we want to default start_date to patient's date of birth when calling create_relationship

    # Existing user
    if isinstance(caregiver, caregiver_models.CaregiverProfile):
        # Note: existing users are not issued a registration code

        caregiver_profile = caregiver
        relationship = create_relationship(patient, caregiver_profile, relationship_type, status)

        # For existing users registering as self, upgrade their legacy UserType to 'Patient'
        if relationship_type.role_type == RoleType.SELF:
            if not caregiver.legacy_id:
                raise ValueError('Legacy ID is missing from Caregiver Profile')

            legacy_utils.update_legacy_user_type(caregiver.legacy_id, LegacyUserType.PATIENT)

        # For existing users (who won't be going through the registration site), init patient data if needed
        if is_new_patient:
            initialize_new_opal_patient(mrns, patient.uuid)
    else:
        # New user
        # Create caregiver and caregiver profile
        caregiver_profile = create_caregiver_profile(
            first_name=caregiver[0],
            last_name=caregiver[1],
        )
        relationship = create_relationship(patient, caregiver_profile, relationship_type, status)
        registration_code = create_registration_code(relationship)

    return relationship, registration_code
