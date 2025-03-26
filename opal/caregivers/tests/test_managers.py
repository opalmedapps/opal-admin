import pytest

from opal.patients import factories as patient_factory
from opal.patients.models import Relationship
from opal.users.models import Caregiver

pytestmark = pytest.mark.django_db


def test_caregiver_patient_list_query() -> None:  # noqa: WPS218
    """Test the query to get the list of patients for a given caregiver."""
    relationship_type = patient_factory.RelationshipType(name='Mother')
    relationship = patient_factory.Relationship(type=relationship_type)
    caregiver = Caregiver.objects.get()
    query_result = Relationship.objects.get_patient_list_for_caregiver(caregiver.username)
    assert query_result[0].patient_id == relationship.patient_id
    assert query_result[0].caregiver_id == relationship.caregiver_id
    assert query_result[0].type_id == relationship_type.id
    assert query_result[0].type.name == relationship_type.name
    assert query_result[0].type.can_answer_questionnaire == relationship_type.can_answer_questionnaire
    assert query_result[0].type.role_type == relationship_type.role_type
    assert relationship.type_id == relationship_type.id
