import pytest
from rest_framework import serializers

from opal.patients.factories import HospitalPatient

from ..api.serializers import QuestionnaireReportRequestSerializer

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


# serializer for the questionnaire report generation API endpoint: questionnaires/reviewed/

def test_mrn_type_for_questionnaire_report() -> None:
    """Ensure `mrn` for the questionnaire report request is a `serializers.CharField` type."""
    hospital_patient = HospitalPatient()
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': '9999996', 'site_name': hospital_patient.site.name},
    )

    assert isinstance(serializer.fields['mrn'], serializers.CharField)
    assert serializer.is_valid()


def test_site_type_for_questionnaire_report() -> None:
    """Ensure `site_name` for the questionnaire report request is a `serializers.CharField` type."""
    hospital_patient = HospitalPatient()
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': '9999996', 'site_name': hospital_patient.site.name},
    )

    assert isinstance(serializer.fields['site_name'], serializers.CharField)
    assert serializer.is_valid()


def test_patient_mrn_type_invalid() -> None:
    """Ensure `mrn` for the questionnaire report request does not accept invalid types."""
    hospital_patient = HospitalPatient()
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': 0, 'site_name': hospital_patient.site.name},
    )
    assert not serializer.is_valid()


def test_patient_site_type_invalid() -> None:
    """Ensure `site_name` for the questionnaire report request does not accept invalid types."""
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': '9999996', 'site_name': 0},
    )
    assert not serializer.is_valid()
