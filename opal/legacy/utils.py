"""Utility functions used by legacy API views."""
import datetime as dt

from django.db.models import F  # noqa: WPS347 (vague import)

from opal.patients.models import HospitalPatient, Patient

from .models import (
    LegacyAccessLevel,
    LegacyLanguage,
    LegacyPatient,
    LegacyPatientControl,
    LegacyPatientHospitalIdentifier,
    LegacySexType,
    LegacyUsers,
)


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
        usertype='Patient',
    ).first()
    if user:
        return user.usertypesernum
    return 0


def update_legacy_user_type(caregiver_legacy_id: int, new_type: str) -> None:
    """
    Update a user's UserType in the legacy Users table.

    Args:
        caregiver_legacy_id: The user's UserSerNum in the legacy Users table.
        new_type: The new UserType to set for the user.
    """
    LegacyUsers.objects.filter(usersernum=caregiver_legacy_id).update(usertype=new_type)


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


def insert_hospital_identifiers(legacy_id: int) -> None:
    """
    Insert the legacy hospital identifiers for the patient.

    Args:
        legacy_id: the legacy ID of the patient
    """
    hospital_identifiers = [
        LegacyPatientHospitalIdentifier(
            patient_id=legacy_id,
            mrn=hospital_patient.mrn,
            is_active=hospital_patient.is_active,
            hospital_id=hospital_patient.site_code,
        )
        for hospital_patient in HospitalPatient.objects.select_related('site').annotate(site_code=F('site__code'))
    ]
    LegacyPatientHospitalIdentifier.objects.bulk_create(hospital_identifiers)


def create_patient_control(legacy_id: int) -> None:
    """
    Create the patient control for the patient.

    Args:
        legacy_id: the legacy ID of the patient
    """
    LegacyPatientControl.objects.create(patient_id=legacy_id)
