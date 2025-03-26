"""Collection of serializers for the app ApiViews."""

from rest_framework import serializers

from opal.legacy.models import LegacyAppointment
from opal.patients.models import HospitalPatient


class LegacyAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for the `LegacyAppointment` model."""

    checkinpossible = serializers.IntegerField(
        source='aliasexpressionsernum.aliassernum.appointmentcheckin.checkinpossible',
    )

    class Meta:
        model = LegacyAppointment
        fields = ['appointmentsernum', 'state', 'scheduledstarttime', 'checkin', 'checkinpossible']


class QuestionnaireReportRequestSerializer(serializers.Serializer):
    """This class defines how a `QuestionnairesReport` request data are serialized."""

    mrn = serializers.CharField(max_length=10, label='MRN')  # TODO: min_length?
    site = serializers.CharField(max_length=10)  # TODO: min_length?

    def validate_mrn(self, value: str) -> str:
        """Check that medical record number (MRN) exists in the OpalDB.

        Args:
            value (str): MRN to be validated

        Returns:
            validated MRN value

        Raises:
            ValidationError: if provided MRN does not exist in the database
        """
        if not HospitalPatient.objects.filter(mrn=value).exists():
            raise serializers.ValidationError('Provided MRN does not exist.')
        return value

    def validate_site(self, value: str) -> str:
        """Check that site code exists in the OpalDB (e.g., MGH).

        Args:
            value (str): site code to be validated

        Returns:
            validated site code value

        Raises:
            ValidationError: if provided site code does not exist in the database
        """
        if not HospitalPatient.objects.filter(site__code=value).exists():
            raise serializers.ValidationError('Provided site code does not exist.')
        return value


class UnreadCountSerializer(serializers.Serializer):
    """Serializer a dictionary having several key-value pairs."""

    unread_appointment_count = serializers.IntegerField()
    unread_document_count = serializers.IntegerField()
    unread_txteammessage_count = serializers.IntegerField()
    unread_educationalmaterial_count = serializers.IntegerField()
    unread_questionnaire_count = serializers.IntegerField()


class AnnouncementUnreadCountSerializer(serializers.Serializer):
    """Serializer for the unread count of Announcement queryset."""

    unread_announcement_count = serializers.IntegerField(min_value=0)
