import pytest
from rest_framework import serializers

from opal.legacy.api.serializers import (
    AnnouncementUnreadCountSerializer,
    QuestionnaireReportRequestSerializer,
    UnreadCountSerializer,
)
from opal.patients.factories import HospitalPatient

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


# serializer for the questionnaire report generation API endpoint: questionnaires/reviewed/

def test_mrn_type_for_questionnaire_report() -> None:
    """Ensure `mrn` for the questionnaire report request is a `serializers.CharField` type."""
    hospital_patient = HospitalPatient()
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': '9999996', 'site': hospital_patient.site.code},
    )

    assert isinstance(serializer.fields['mrn'], serializers.CharField)
    assert serializer.is_valid()


def test_site_type_for_questionnaire_report() -> None:
    """Ensure `site_name` for the questionnaire report request is a `serializers.CharField` type."""
    hospital_patient = HospitalPatient()
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': '9999996', 'site': hospital_patient.site.code},
    )

    assert isinstance(serializer.fields['site'], serializers.CharField)
    assert serializer.is_valid()


def test_patient_mrn_type_invalid() -> None:
    """Ensure `mrn` for the questionnaire report request does not accept invalid types."""
    hospital_patient = HospitalPatient()
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': 0, 'site': hospital_patient.site.code},
    )
    assert not serializer.is_valid()


def test_patient_site_type_invalid() -> None:
    """Ensure `site_name` for the questionnaire report request does not accept invalid types."""
    serializer = QuestionnaireReportRequestSerializer(
        data={'mrn': '9999996', 'site': 0},
    )
    assert not serializer.is_valid()


def test_valid_serializer() -> None:
    """Test if the serializer is valid."""
    unread_count = {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
        'unread_questionnaire_count': 223,
    }
    unread_serializer = UnreadCountSerializer(data=unread_count)
    assert unread_serializer.is_valid()
    assert unread_serializer.validated_data == {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
        'unread_questionnaire_count': 223,
    }
    assert unread_serializer.data == {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
        'unread_questionnaire_count': 223,
    }


def test_invalid_serializer() -> None:
    """Test if the serializer is invalid."""
    unread_count = {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
    }
    unread_serializer = UnreadCountSerializer(data=unread_count)
    assert not unread_serializer.is_valid()
    assert unread_serializer.data == {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
    }
    assert unread_serializer.errors == {'unread_questionnaire_count': ['This field is required.']}


def test_invalid_field_value_type() -> None:
    """Test if the serializer field value type is invalid."""
    unread_count = {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
        'unread_questionnaire_count': 'ffff',
    }
    unread_serializer = UnreadCountSerializer(data=unread_count)
    assert not unread_serializer.is_valid()
    assert unread_serializer.errors == {'unread_questionnaire_count': ['A valid integer is required.']}


def test_invalid_datatype() -> None:
    """Test if the serializer data type is invalid."""
    unread_count = {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
        'unread_questionnaire_count': 223,
    }
    unread_serializer = UnreadCountSerializer(data=[unread_count])
    assert not unread_serializer.is_valid()
    assert unread_serializer.errors == {'non_field_errors': ['Invalid data. Expected a dictionary, but got list.']}


def test_data_access_before_save_raises_error() -> None:
    """Test if the serializer data is saved without error."""
    unread_count = {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
        'unread_questionnaire_count': 223,
    }
    unread_serializer = UnreadCountSerializer(data=unread_count)
    assert unread_serializer.is_valid()
    assert unread_serializer.data == {
        'unread_appointment_count': 5,
        'unread_document_count': 655,
        'unread_txteammessage_count': 1964,
        'unread_educationalmaterial_count': 2020,
        'unread_questionnaire_count': 223,
    }
    with pytest.raises(AssertionError):
        unread_serializer.save()


def test_valid_announcement_serializer() -> None:
    """Test if the announcement serializer is valid."""
    unread_count = {
        'unread_announcement_count': 5,
    }
    unread_serializer = AnnouncementUnreadCountSerializer(data=unread_count)
    assert unread_serializer.is_valid()
    assert unread_serializer.validated_data == unread_count
    assert unread_serializer.data == unread_count


def test_invalid_announcement_serializer() -> None:
    """Test if the announcement serializer is invalid."""
    unread_serializer = AnnouncementUnreadCountSerializer(data={})
    assert not unread_serializer.is_valid()
    assert unread_serializer.errors == {'unread_announcement_count': ['This field is required.']}


def test_invalid_announcement_field_value_type() -> None:
    """Test if the announcement serializer field value type is invalid."""
    unread_count = {
        'unread_announcement_count': 'a',
    }
    unread_serializer = AnnouncementUnreadCountSerializer(data=unread_count)
    assert not unread_serializer.is_valid()
    assert unread_serializer.data == unread_count
    assert unread_serializer.errors == {'unread_announcement_count': ['A valid integer is required.']}


def test_invalid_announcement_datatype() -> None:
    """Test if the serializer data type is invalid."""
    unread_count = {
        'unread_announcement_count': 5,
    }
    unread_serializer = AnnouncementUnreadCountSerializer(data=[unread_count])
    assert not unread_serializer.is_valid()
    assert unread_serializer.errors == {'non_field_errors': ['Invalid data. Expected a dictionary, but got list.']}


def test_invalid_announcement_field_min_value() -> None:
    """Test if the announcement serializer field value type is invalid."""
    unread_count = {
        'unread_announcement_count': '-1',
    }
    unread_serializer = AnnouncementUnreadCountSerializer(data=unread_count)
    assert not unread_serializer.is_valid()
    assert unread_serializer.data == unread_count
    assert unread_serializer.errors == {
        'unread_announcement_count': ['Ensure this value is greater than or equal to 0.'],
    }


def test_announcement_data_access_before_save() -> None:
    """Test if the announcement serializer data is saved without error."""
    unread_count = {
        'unread_announcement_count': 5,
    }
    unread_serializer = AnnouncementUnreadCountSerializer(data=unread_count)
    assert unread_serializer.is_valid()
    assert unread_serializer.data == unread_count
    with pytest.raises(AssertionError):
        unread_serializer.save()
