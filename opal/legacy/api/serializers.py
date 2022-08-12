"""Collection of serializers for the app ApiViews."""

from rest_framework import serializers

from opal.legacy.models import LegacyAppointment, LegacyPatient


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

    patient_id = serializers.IntegerField()

    def validate_patient_id(self, value: int) -> bool:
        """Check that patient id (PatientSerNum) exists in the OpalDB.

        Args:
            value (int): patient id (PatientSerNum) to be validated

        Returns:
            Boolean value showing the result of the patient id validation
        """
        return LegacyPatient.objects.filter(patientsernum=value).exists()
