"""Collection of serializers for the app ApiViews."""
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


class UnreadCountSerializer(serializers.Serializer):
    """Serializer a dictionary having several key-value pairs."""

    unread_appointment_count = serializers.IntegerField()
    unread_document_count = serializers.IntegerField()
    unread_txteammessage_count = serializers.IntegerField()
    unread_educationalmaterial_count = serializers.IntegerField()
    unread_questionnaire_count = serializers.IntegerField()


class AnnouncementUnreadCountSerializer(serializers.Serializer):
    """Serializer for the unread count of Announcement queryset."""

    unread_announcement_count = serializers.IntegerField()
