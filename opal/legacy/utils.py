"""Utility functions used by legacy API views."""
import datetime as dt
from types import MappingProxyType

from django.utils import timezone

from opal.caregivers.models import CaregiverProfile
from opal.hospital_settings.models import Site
from opal.patients.models import Patient

from .models import (
    LegacyAccessLevel,
    LegacyLanguage,
    LegacyPatient,
    LegacyPatientControl,
    LegacyPatientHospitalIdentifier,
    LegacySexType,
    LegacyUsers,
    LegacyUserType,
)

#: Mapping from sex type to the corresponding legacy sex type
SEX_TYPE_MAPPING = MappingProxyType({
    Patient.SexType.MALE.value: LegacySexType.MALE,
    Patient.SexType.FEMALE.value: LegacySexType.FEMALE,
    Patient.SexType.OTHER.value: LegacySexType.OTHER,
    Patient.SexType.UNKNOWN.value: LegacySexType.UNKNOWN,
})

#: Mapping from data access type to the corresponding legacy access level
ACCESS_LEVEL_MAPPING = MappingProxyType({
    Patient.DataAccessType.ALL.value: LegacyAccessLevel.ALL,
    Patient.DataAccessType.NEED_TO_KNOW.value: LegacyAccessLevel.NEED_TO_KNOW,
})


def get_patient_sernum(username: str) -> int:
    """
    Get the patient sernum associated with the username to query the legacy database.

    Args:
        username: Firebase username making the request

    Returns:
        User patient sernum associated with the request username user name.
    """
    user = LegacyUsers.objects.filter(
        username=username,
        usertype=LegacyUserType.PATIENT,
    ).first()
    if user:
        return user.usertypesernum
    return 0


def create_patient(  # noqa: WPS211 (too many arguments)
    first_name: str,
    last_name: str,
    sex: LegacySexType,
    date_of_birth: dt.date,
    email: str,
    language: LegacyLanguage,
    ramq: str,
    access_level: LegacyAccessLevel,
) -> LegacyPatient:
    """
    Create a patient with the given properties.

    Args:
        first_name: the first name of the patient
        last_name: the last name of the patient
        sex: the sex of the patient
        date_of_birth: the date of birth of the patient
        email: the email of the patient
        language: the language of the patient
        ramq: the RAMQ of the patient
        access_level: the access level of the patient

    Returns:
        the legacy patient instance
    """
    age = Patient.calculate_age(date_of_birth)

    patient = LegacyPatient(
        first_name=first_name,
        last_name=last_name,
        sex=sex,
        date_of_birth=date_of_birth,
        age=age,
        email=email,
        language=language,
        ramq=ramq,
        access_level=access_level,
    )
    patient.full_clean()
    patient.save()

    return patient


def update_patient(patient: LegacyPatient, sex: LegacySexType, date_of_birth: dt.date, ramq: str) -> None:
    """
    Update an existing patient with the given properties.

    Args:
        patient: the patient to update
        sex: the sex of the patient
        date_of_birth: the date of birth of the patient
        ramq: the RAMQ of the patient
    """
    age = Patient.calculate_age(date_of_birth)

    patient.sex = sex
    patient.date_of_birth = date_of_birth
    patient.age = age
    patient.ramq = ramq
    patient.full_clean()
    patient.save()


def insert_hospital_identifiers(patient: LegacyPatient, mrns: list[tuple[Site, str, bool]]) -> None:
    """
    Insert legacy hospital identifiers for the patient.

    Args:
        patient: the legacy patient
        mrns: list of MRN tuples consisting of the site, MRN and whether the MRN is active
    """
    hospital_identifiers = [
        LegacyPatientHospitalIdentifier(
            patient=patient,
            mrn=hospital_patient[1],
            is_active=hospital_patient[2],
            hospital_id=hospital_patient[0].acronym,
        )
        for hospital_patient in mrns
    ]
    LegacyPatientHospitalIdentifier.objects.bulk_create(hospital_identifiers)


def create_patient_control(patient: LegacyPatient) -> None:
    """
    Create the patient control for the patient.

    Args:
        patient: the legacy patient
    """
    LegacyPatientControl.objects.create(patient=patient)


def initialize_new_patient(
    patient: Patient,
    mrns: list[tuple[Site, str, bool]],
    self_caregiver: CaregiverProfile | None,
) -> LegacyPatient:
    """
    Initialize a new legacy patient based on an existing patient.

    Creates the legacy patient, inserts the hospital identifiers, and creates the patient control.

    Args:
        patient: the existing patient to initialize a legacy patient instance from
        mrns: list of MRN tuples consisting of the site, MRN and whether the MRN is active
        self_caregiver: the caregiver profile instance if the patient is their own caregiver, otherwise None

    Returns:
        the legacy patient
    """
    date_of_birth = dt.datetime.combine(patient.date_of_birth, dt.time())
    email = self_caregiver.user.email if self_caregiver else ''
    language = LegacyLanguage(self_caregiver.user.language.upper()) if self_caregiver else LegacyLanguage.FRENCH

    legacy_patient = create_patient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        sex=SEX_TYPE_MAPPING[patient.sex],
        date_of_birth=timezone.make_aware(date_of_birth),
        email=email,
        language=language,
        ramq=patient.ramq,
        access_level=ACCESS_LEVEL_MAPPING[patient.data_access],
    )

    insert_hospital_identifiers(legacy_patient, mrns)
    create_patient_control(legacy_patient)

    return legacy_patient


def update_legacy_user_type(caregiver_legacy_id: int, new_type: LegacyUserType) -> None:
    """
    Update a user's UserType in the legacy Users table.

    Args:
        caregiver_legacy_id: The user's UserSerNum in the legacy Users table.
        new_type: The new UserType to set for the user.
    """
    LegacyUsers.objects.filter(usersernum=caregiver_legacy_id).update(usertype=new_type)
