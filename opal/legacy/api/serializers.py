"""Collection of serializers for the app ApiViews."""
from typing import Dict

from rest_framework import serializers

from opal.legacy.models import LegacyAppointment


class LegacyAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for the `LegacyAppointment` model."""

    checkinpossible = serializers.IntegerField(
        source='aliasexpressionsernum.aliassernum.appointmentcheckin.checkinpossible',
    )

    class Meta:
        model = LegacyAppointment
        fields = ['appointmentsernum', 'state', 'scheduledstarttime', 'checkin', 'checkinpossible']


class UnreadCount:
    """Create an UnreadCount object for all the unread counts needed."""

    def __init__(  # noqa: WPS211
        self,
        unread_appointment_count: int,
        unread_document_count: int,
        unread_txteammessage_count: int,
        unread_educationalmaterial_count: int,
        unread_questionnaire_count: int,
    ) -> None:
        """Initialize unread counts object.

        Args:
            unread_appointment_count: appointment unread count
            unread_document_count: document unread count
            unread_txteammessage_count: treatment team message unread count
            unread_educationalmaterial_count: educational material unread count
            unread_questionnaire_count: questionnaire unread count
        """
        self.unread_appointment_count = unread_appointment_count
        self.unread_document_count = unread_document_count
        self.unread_txteammessage_count = unread_txteammessage_count
        self.unread_educationalmaterial_count = unread_educationalmaterial_count
        self.unread_questionnaire_count = unread_questionnaire_count


class UnreadCountSerializer(serializers.Serializer):
    """Serializer for an UnreadCount object."""

    unread_appointment_count = serializers.IntegerField()
    unread_document_count = serializers.IntegerField()
    unread_txteammessage_count = serializers.IntegerField()
    unread_educationalmaterial_count = serializers.IntegerField()
    unread_questionnaire_count = serializers.IntegerField()

    def validate(self, data: Dict) -> Dict:
        """
        Check that data member is integer or not.

        Args:
            data: a dictionary of field values

        Raises:
            ValidationError: the field values are wrong type

        Returns:
            the data object if not catching error
        """
        if (
            isinstance(data['unread_appointment_count'], int)  # noqa: WPS222
            and isinstance(data['unread_document_count'], int)
            and isinstance(data['unread_txteammessage_count'], int)
            and isinstance(data['unread_educationalmaterial_count'], int)
            and isinstance(data['unread_questionnaire_count'], int)
        ):
            raise serializers.ValidationError('Field values must be the integer')
        return data
