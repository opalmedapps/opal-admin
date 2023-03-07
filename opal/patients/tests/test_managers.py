import pytest

from ..managers import RelationshipTypeManager
from ..models import RoleType

pytestmark = pytest.mark.django_db


def test_relationshiptype_manager_self_type() -> None:
    """Ensure the RelationshipTypeManager returns the self type."""
    assert RelationshipTypeManager().self_type().role_type == RoleType.SELF


def test_relationshiptype_manager_parent_guardian_type() -> None:
    """Ensure the RelationshipTypeManager returns the parent/guardian type."""
    assert RelationshipTypeManager().parent_guardian().role_type == RoleType.PARENT_GUARDIAN


def test_relationshiptype_manager_guardian_caregiver_type() -> None:
    """Ensure the RelationshipTypeManager returns the guardian-caregiver type."""
    assert RelationshipTypeManager().guardian_caregiver().role_type == RoleType.GUARDIAN_CAREGIVER


def test_relationshiptype_manager_mandatary_type() -> None:
    """Ensure the RelationshipTypeManager returns the mandatary type."""
    assert RelationshipTypeManager().mandatary().role_type == RoleType.MANDATARY
