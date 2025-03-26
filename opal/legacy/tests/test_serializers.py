import pytest
from rest_framework import serializers

from ..api.serializers import QuestionnaireReportRequestSerializer

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


# serializer for the questionnaire report generation API endpoint: questionnaires/reviewed/

def test_patient_id_type_for_questionnaire_report() -> None:
    """Ensure `patient_id` for the questionnaire report request is a `serializers.IntegerField` type."""
    serializer = QuestionnaireReportRequestSerializer(
        data={'patient_id': 51},
    )

    assert isinstance(serializer.fields['patient_id'], serializers.IntegerField)
    serializer.run_validation()
    assert serializer.is_valid()


def test_patient_id_type_invalid() -> None:
    """Ensure `patient_id` for the questionnaire report request does not accept invalid types."""
    serializer = QuestionnaireReportRequestSerializer(
        data={'patient_id': 'invalid type'},
    )
    assert not serializer.is_valid()
