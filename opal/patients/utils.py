"""App patients util functions."""
from datetime import date
from typing import Any, Optional, Union

from django import forms
from django.db.models import QuerySet
from django.utils import timezone

from opal.caregivers import models as caregiver_models
from opal.users.models import User

#: The indicator of the female sex within the RAMQ number (added to the month)
from ..hospital_settings.models import Site
from . import constants
from .models import Patient, Relationship, RelationshipType, RoleType

RAMQ_FEMALE_INDICATOR = 50


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


def update_caregiver(user: User, info: dict) -> None:
    """
    Update User information.

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


def is_mrn_or_single_site(form: forms.Form) -> Any:
    """
    Check a form object that has a `card_type` field
    Args:
        form: AccessRequestManagementForm

    Returns:
        True if there is only one site or the selected `card_type` is MRN, False otherwise
    """
    return form['card_type'].value() != constants.MedicalCard.mrn.name or Site.objects.all().count() == 1  # noqa: WPS221
