"""App patients util functions."""
from django.utils import timezone

from opal.caregivers import models as caregiver_models
from opal.users.models import User

from .models import Patient


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


def update_caregiver(user: User, info: dict) -> None:
    """
    Update User infomation.

    Args:
        user: User object
        info: User info to be updated
    """
    user.language = info['user']['language']
    user.phone_number = info['user']['phone_number']
    user.date_joined = timezone.now()
    user.is_active = True
    user.full_clean()
    user.save()


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
