import pytest

from ..models import RelationshipType, RoleType

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
