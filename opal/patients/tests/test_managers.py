import pytest

from opal.caregivers import factories as caregiver_factories
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models
from opal.users import factories as user_factories

from ..models import Relationship, RelationshipType, RoleType

pytestmark = pytest.mark.django_db


def test_relationshiptype_manager_self_type() -> None:
    """Ensure the RelationshipTypeManager returns the self type."""
    assert RelationshipType.objects.self_type().role_type == RoleType.SELF


def test_relationshiptype_manager_parent_guardian_type() -> None:
    """Ensure the RelationshipTypeManager returns the parent/guardian type."""
    assert RelationshipType.objects.parent_guardian().role_type == RoleType.PARENT_GUARDIAN


def test_relationshiptype_manager_guardian_caregiver_type() -> None:
    """Ensure the RelationshipTypeManager returns the guardian-caregiver type."""
    assert RelationshipType.objects.guardian_caregiver().role_type == RoleType.GUARDIAN_CAREGIVER


def test_relationshiptype_manager_mandatary_type() -> None:
    """Ensure the RelationshipTypeManager returns the mandatary type."""
    assert RelationshipType.objects.mandatary().role_type == RoleType.MANDATARY


def test_get_patient_id_list_for_any_caregiver() -> None:
    """Get Patient is list from caregivers with any relationship status."""
    caregiver = user_factories.Caregiver()
    profile = caregiver_factories.CaregiverProfile(user=caregiver)
    patient1 = patient_factories.Patient()
    patient_factories.Relationship(
        patient=patient1,
        caregiver=profile,
        status=patient_models.RelationshipStatus.REVOKED,
    )
    patient2 = patient_factories.Patient()
    patient_factories.Relationship(
        patient=patient2,
        caregiver=profile,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    patient_ids = Relationship.objects.get_list_of_patients_ids_for_caregiver(caregiver.username)

    assert len(patient_ids) == 2


def test_get_patient_id_list_for_confirmed_caregiver() -> None:
    """Get Patient is list from caregivers with confirmed relationship status only."""
    caregiver = user_factories.Caregiver()
    profile = caregiver_factories.CaregiverProfile(user=caregiver)
    patient1 = patient_factories.Patient()
    patient_factories.Relationship(
        patient=patient1,
        caregiver=profile,
        status=patient_models.RelationshipStatus.REVOKED,
    )
    patient2 = patient_factories.Patient()
    patient_factories.Relationship(
        patient=patient2,
        caregiver=profile,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )
    patient_ids = Relationship.objects.get_list_of_patients_ids_for_caregiver(
        username=caregiver.username,
        status=patient_models.RelationshipStatus.CONFIRMED,
    )

    assert len(patient_ids) == 1
