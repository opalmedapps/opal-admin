"""Utility functions used by legacy API views."""
from django.db.models import F  # noqa: WPS347 (vague import)

from opal.patients.models import HospitalPatient

from .models import LegacyPatientControl, LegacyPatientHospitalIdentifier, LegacyUsers


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
