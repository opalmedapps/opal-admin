import pytest

from opal.legacy.api.serializers import UnreadCountSerializer

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


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
    """Test if the serializer data type is invalid."""
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
